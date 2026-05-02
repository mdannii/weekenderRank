import json
import os
import uuid
from flask import Flask, request, jsonify, render_template_string, session

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "weekender_secret_key_123")  # Use env var in production
DATA_FILE = "rankings.json"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

# --- Data Management ---

def load_data():
    if not os.path.exists(DATA_FILE):
        # Initial Roster
        initial_players = [
            "Aaron Chen", "Bella Wu", "Chris Zhang", "David Lim", "Emma Watson",
            "Felix Ng", "Grace Ho", "Henry Tan", "Iris Wong", "Jacky Lee",
            "Kevin Low", "Linda Koh", "Mike Sim", "Nancy Tay", "Oscar Quek",
            "Penny Seah", "Quincy Phua", "Ryan Teo", "Sarah Ong", "Toby Yeo"
        ]
        data = {
            "players": [{"id": str(uuid.uuid4()), "name": name} for name in initial_players],
            "submissions": {} # player_id: { playerName: score }
        }
        save_data(data)
        return data
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- Routes ---

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/data", methods=["GET"])
def get_data():
    data = load_data()
    voter_id = session.get("voter_id")
    return jsonify({
        "players": data["players"],
        "submissions": data["submissions"],
        "voter_id": voter_id,
        "my_vote": data["submissions"].get(voter_id) if voter_id else None
    })

@app.route("/api/identify", methods=["POST"])
def identify():
    player_id = request.json.get("player_id")
    data = load_data()
    
    # Verify player exists
    if any(p["id"] == player_id for p in data["players"]):
        session["voter_id"] = player_id
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid player"}), 400

@app.route("/api/vote", methods=["POST"])
def submit_vote():
    voter_id = session.get("voter_id")
    if not voter_id:
        return jsonify({"error": "Identity not selected"}), 401
        
    ratings = request.json.get("ratings")
    if not ratings:
        return jsonify({"error": "No ratings provided"}), 400
    
    data = load_data()
    data["submissions"][voter_id] = ratings
    save_data(data)
    return jsonify({"success": True})

@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    password = request.json.get("password")
    if password == ADMIN_PASSWORD:
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Incorrect password"}), 401

@app.route("/api/admin/players", methods=["POST"])
def add_player():
    name = request.json.get("name")
    if not name:
        return jsonify({"error": "Name is required"}), 400
    
    data = load_data()
    if any(p["name"].lower() == name.lower() for p in data["players"]):
        return jsonify({"error": "Player already exists"}), 400
        
    data["players"].append({"id": str(uuid.uuid4()), "name": name.strip()})
    data["players"].sort(key=lambda x: x["name"])
    save_data(data)
    return jsonify({"success": True})

@app.route("/api/admin/players/<player_id>", methods=["DELETE"])
def delete_player(player_id):
    data = load_data()
    data["players"] = [p for p in data["players"] if p["id"] != player_id]
    # Remove their submission if they were deleted
    if player_id in data["submissions"]:
        del data["submissions"][player_id]
    save_data(data)
    return jsonify({"success": True})

# --- Frontend Template ---

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WeekenderRank</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        .slide-up { animation: slideUp 0.4s ease-out; }
        @keyframes slideUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        input[type=range]::-webkit-slider-thumb {
            -webkit-appearance: none;
            height: 24px; width: 24px; border-radius: 50%;
            background: #4f46e5; cursor: pointer; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
    </style>
</head>
<body class="bg-slate-50 text-slate-900 font-sans pb-24">

    <!-- Header -->
    <header class="bg-white border-b border-slate-200 sticky top-0 z-20 px-6 py-4 shadow-sm">
        <div class="flex items-center justify-between max-w-2xl mx-auto">
            <h1 class="text-xl font-bold tracking-tight flex items-center gap-2 text-indigo-600">
                <i data-lucide="trophy"></i> WeekenderRank
            </h1>
            <div class="flex items-center gap-2">
                <button id="adminBtn" class="p-2 bg-slate-100 rounded-full text-slate-500 hover:bg-slate-200">
                    <i data-lucide="lock" size="20"></i>
                </button>
            </div>
        </div>
    </header>

    <main id="app" class="max-w-2xl mx-auto px-4 py-6">
        <!-- Views will be injected here by JavaScript -->
        <div id="view-container" class="slide-up"></div>
    </main>

    <!-- Navigation -->
    <nav class="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 py-3 flex justify-around shadow-[0_-4px_10px_rgba(0,0,0,0.02)]">
        <button onclick="switchTab('poll')" class="nav-item flex flex-col items-center gap-1 text-indigo-600" id="nav-poll">
            <i data-lucide="star"></i>
            <span class="text-[10px] font-bold uppercase">Rate</span>
        </button>
        <button onclick="switchTab('results')" class="nav-item flex flex-col items-center gap-1 text-slate-400" id="nav-results">
            <i data-lucide="bar-chart-2"></i>
            <span class="text-[10px] font-bold uppercase">Rank</span>
        </button>
    </nav>

    <!-- Admin Login Modal -->
    <div id="loginModal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 hidden items-center justify-center p-4">
        <div class="bg-white w-full max-w-sm rounded-3xl p-8 shadow-2xl space-y-6">
            <div class="flex justify-between items-start">
                <div class="p-3 bg-indigo-50 text-indigo-600 rounded-2xl"><i data-lucide="lock"></i></div>
                <button onclick="toggleModal('loginModal', false)" class="text-slate-400"><i data-lucide="x"></i></button>
            </div>
            <div>
                <h3 class="text-xl font-bold">Admin Access</h3>
                <p class="text-slate-500 text-sm">Enter password to manage players.</p>
            </div>
            <input type="password" id="adminPassword" placeholder="Password" class="w-full px-4 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 outline-none">
            <button onclick="handleAdminLogin()" class="w-full py-4 bg-indigo-600 text-white font-bold rounded-2xl shadow-lg hover:bg-indigo-700">Unlock</button>
        </div>
    </div>

    <script>
        let state = {
            players: [],
            submissions: {},
            voterId: null,
            myVote: null,
            activeTab: 'poll',
            currentPollIndex: 0,
            tempRatings: {},
            isAdmin: false,
            isEditing: false
        };

        async function fetchData() {
            const res = await fetch('/api/data');
            const data = await res.json();
            state.players = data.players;
            state.submissions = data.submissions;
            state.voterId = data.voter_id;
            state.myVote = data.my_vote;
            
            if (state.myVote && !state.isEditing) {
                state.tempRatings = { ...state.myVote };
            } else if (!state.tempRatings || Object.keys(state.tempRatings).length === 0) {
                state.players.forEach(p => {
                   if (!state.tempRatings[p.name]) state.tempRatings[p.name] = 5;
                });
            }
            render();
        }

        function switchTab(tab) {
            state.activeTab = tab;
            document.querySelectorAll('.nav-item').forEach(el => el.classList.replace('text-indigo-600', 'text-slate-400'));
            document.getElementById(`nav-${tab}`).classList.replace('text-slate-400', 'text-indigo-600');
            render();
        }

        function toggleModal(id, show) {
            const el = document.getElementById(id);
            if (show) el.classList.remove('hidden'); else el.classList.add('hidden');
            if (show) el.classList.add('flex'); else el.classList.remove('flex');
        }

        async function handleAdminLogin() {
            const password = document.getElementById('adminPassword').value;
            const res = await fetch('/api/admin/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ password })
            });
            if (res.ok) {
                state.isAdmin = true;
                toggleModal('loginModal', false);
                switchTab('admin');
            } else {
                alert("Incorrect password");
            }
        }

        async function identifyPlayer(playerId) {
            const res = await fetch('/api/identify', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ player_id: playerId })
            });
            if (res.ok) {
                fetchData();
            }
        }

        async function submitPoll() {
            await fetch('/api/vote', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ ratings: state.tempRatings })
            });
            state.isEditing = false;
            fetchData();
        }

        async function addPlayer(name) {
            if (!name) return;
            await fetch('/api/admin/players', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name })
            });
            fetchData();
        }

        async function deletePlayer(id) {
            await fetch(`/api/admin/players/${id}`, { method: 'DELETE' });
            fetchData();
        }

        function render() {
            const container = document.getElementById('view-container');
            container.innerHTML = '';
            
            if (state.activeTab === 'poll') {
                // If not identified yet, show selection screen
                if (!state.voterId) {
                    // Find which players have already voted to mark them (optional UX)
                    const votedIds = Object.keys(state.submissions);
                    
                    container.innerHTML = `
                        <div class="bg-white p-8 rounded-3xl shadow-sm border border-slate-100 text-center space-y-6">
                            <div class="w-16 h-16 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto">
                                <i data-lucide="user-check"></i>
                            </div>
                            <div>
                                <h2 class="text-2xl font-bold">Who are you?</h2>
                                <p class="text-slate-500 text-sm mt-1">Please select your name to start the poll.</p>
                            </div>
                            <select id="playerSelect" class="w-full px-4 py-4 bg-slate-50 border border-slate-200 rounded-2xl outline-none focus:ring-2 focus:ring-indigo-500 appearance-none">
                                <option value="" disabled selected>Select your name...</option>
                                ${state.players.map(p => `
                                    <option value="${p.id}">${p.name} ${votedIds.includes(p.id) ? '(Update previous)' : ''}</option>
                                `).join('')}
                            </select>
                            <button onclick="identifyPlayer(document.getElementById('playerSelect').value)" class="w-full py-4 bg-indigo-600 text-white font-bold rounded-2xl shadow-lg hover:bg-indigo-700">Start Polling</button>
                        </div>
                    `;
                } else if (state.myVote && !state.isEditing) {
                    container.innerHTML = `
                        <div class="flex flex-col items-center justify-center py-12 text-center">
                            <div class="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center text-green-600 mb-6">
                                <i data-lucide="check-circle-2" size="48"></i>
                            </div>
                            <h2 class="text-2xl font-bold mb-2">Rankings Recorded</h2>
                            <p class="text-slate-500 mb-8 max-w-xs">Identity: <span class="font-bold text-slate-800">${state.players.find(p=>p.id===state.voterId)?.name}</span><br>You've already submitted your ratings. You can update them at any time.</p>
                            <div class="flex flex-col gap-3 w-full">
                                <button onclick="state.isEditing=true; render();" class="w-full bg-indigo-600 text-white py-4 rounded-2xl font-bold shadow-lg">Update My Ratings</button>
                                <button onclick="state.voterId=null; render();" class="text-slate-400 text-xs font-bold py-2">Change Identity</button>
                            </div>
                        </div>
                    `;
                } else if (state.players.length === 0) {
                    container.innerHTML = `<p class="text-center py-20 text-slate-400">Waiting for players to be added...</p>`;
                } else {
                    const p = state.players[state.currentPollIndex];
                    const progress = Math.round(((state.currentPollIndex + 1) / state.players.length) * 100);
                    container.innerHTML = `
                        <div class="bg-white p-6 rounded-3xl shadow-sm border border-slate-100">
                            <div class="flex justify-between items-center mb-6">
                                <span class="text-xs font-bold text-slate-400 uppercase tracking-widest">Player ${state.currentPollIndex + 1} of ${state.players.length}</span>
                                <span class="text-xs font-bold text-indigo-600 bg-indigo-50 px-2 py-1 rounded">${progress}%</span>
                            </div>
                            <div class="flex items-center gap-4 mb-8">
                                <div class="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-2xl flex items-center justify-center text-white text-2xl font-bold">${p.name[0]}</div>
                                <div>
                                    <h2 class="text-2xl font-bold text-slate-800">${p.name}</h2>
                                    <p class="text-slate-400">Rating: <span class="text-indigo-600 font-bold">${state.tempRatings[p.name] || 5}</span></p>
                                </div>
                            </div>
                            <input type="range" min="1" max="10" value="${state.tempRatings[p.name] || 5}" 
                                oninput="state.tempRatings['${p.name}']=this.value; render();"
                                class="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600 mb-4">
                            <div class="flex justify-between text-[10px] font-black text-slate-300 uppercase tracking-tighter mb-8">
                                <span>Novice</span><span>Pro</span>
                            </div>
                            <div class="flex gap-3">
                                ${state.currentPollIndex > 0 ? `<button onclick="state.currentPollIndex--; render();" class="flex-1 py-4 bg-slate-100 font-bold rounded-2xl">Back</button>` : ''}
                                ${state.currentPollIndex < state.players.length - 1 
                                    ? `<button onclick="state.currentPollIndex++; render();" class="flex-[2] py-4 bg-indigo-600 text-white font-bold rounded-2xl shadow-lg">Next</button>`
                                    : `<button onclick="submitPoll()" class="flex-[2] py-4 bg-green-600 text-white font-bold rounded-2xl shadow-lg">Submit All</button>`
                                }
                            </div>
                        </div>
                    `;
                }
            } else if (state.activeTab === 'results') {
                const leaderboard = state.players.map(p => {
                    const scores = Object.values(state.submissions).map(s => s[p.name]).filter(v => v !== undefined);
                    const avg = scores.length ? (scores.reduce((a,b)=>a+parseInt(b),0) / scores.length).toFixed(1) : 0;
                    return { name: p.name, avg };
                }).sort((a,b) => b.avg - a.avg);

                container.innerHTML = `
                    <div class="bg-white p-6 rounded-3xl shadow-sm border border-slate-100">
                        <div class="flex justify-between items-center mb-6">
                            <h2 class="text-xl font-bold">Current Leaderboard</h2>
                            <span class="text-[10px] text-slate-400 font-bold uppercase tracking-widest">${Object.keys(state.submissions).length} Ballots</span>
                        </div>
                        <div class="space-y-6">
                            ${leaderboard.map((p, i) => `
                                <div class="flex items-center gap-4">
                                    <span class="w-6 font-bold text-slate-300">${i+1}</span>
                                    <div class="flex-1">
                                        <div class="flex justify-between mb-1">
                                            <span class="font-semibold text-slate-700">${p.name}</span>
                                            <span class="font-bold text-indigo-600">${p.avg}</span>
                                        </div>
                                        <div class="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                                            <div class="bg-indigo-500 h-full rounded-full transition-all duration-700" style="width: ${p.avg * 10}%"></div>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            } else if (state.activeTab === 'admin') {
                container.innerHTML = `
                    <div class="bg-white p-6 rounded-3xl shadow-sm border border-slate-100">
                        <div class="flex justify-between items-center mb-6">
                            <h2 class="text-xl font-bold">Manage Roster</h2>
                            <button onclick="state.isAdmin=false; switchTab('poll');" class="text-xs text-red-500 font-bold">Logout</button>
                        </div>
                        <div class="flex gap-2 mb-8">
                            <input type="text" id="newPlayerName" placeholder="Player Name" class="flex-1 px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-indigo-500">
                            <button onclick="addPlayer(document.getElementById('newPlayerName').value)" class="p-3 bg-indigo-600 text-white rounded-xl"><i data-lucide="plus"></i></button>
                        </div>
                        <div class="space-y-2">
                            ${state.players.map(p => `
                                <div class="flex justify-between items-center p-4 bg-slate-50 rounded-2xl">
                                    <span class="font-medium">${p.name}</span>
                                    <button onclick="deletePlayer('${p.id}')" class="text-slate-300 hover:text-red-500"><i data-lucide="trash-2" size="18"></i></button>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
            
            lucide.createIcons();
        }

        document.getElementById('adminBtn').onclick = () => {
            if (state.isAdmin) switchTab('admin');
            else toggleModal('loginModal', true);
        };

        window.onload = fetchData;
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    # Get port from environment variable (standard for cloud hosts like Render/Railway)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)