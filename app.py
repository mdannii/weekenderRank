import json
import os
import uuid
from flask import Flask, request, jsonify, render_template_string, session

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "weekender_secret_key_999")
DATA_FILE = "rankings.json"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

# --- Data Management ---

def load_data():
    if not os.path.exists(DATA_FILE):
        # Start with an EMPTY list as requested
        data = {
            "players": [],
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
    data = load_data()
    data["submissions"][voter_id] = ratings
    save_data(data)
    return jsonify({"success": True})

@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    password = request.json.get("password")
    if password == ADMIN_PASSWORD:
        return jsonify({"success": True})
    return jsonify({"success": False}), 401

@app.route("/api/admin/players", methods=["POST"])
def add_player():
    name = request.json.get("name")
    if not name: return jsonify({"error": "Empty name"}), 400
    data = load_data()
    if any(p["name"].lower() == name.strip().lower() for p in data["players"]):
        return jsonify({"error": "Exists"}), 400
    data["players"].append({"id": str(uuid.uuid4()), "name": name.strip()})
    data["players"].sort(key=lambda x: x["name"])
    save_data(data)
    return jsonify({"success": True})

@app.route("/api/admin/players/<player_id>", methods=["DELETE"])
def delete_player(player_id):
    data = load_data()
    data["players"] = [p for p in data["players"] if p["id"] != player_id]
    if player_id in data["submissions"]: del data["submissions"][player_id]
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
            background: #4f46e5; cursor: pointer; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body class="bg-slate-50 text-slate-900 font-sans pb-24">

    <header class="bg-white border-b border-slate-200 sticky top-0 z-20 px-6 py-4">
        <div class="flex items-center justify-between max-w-2xl mx-auto">
            <h1 class="text-xl font-bold tracking-tight flex items-center gap-2 text-indigo-600">
                <i data-lucide="trophy"></i> WeekenderRank
            </h1>
            <button id="adminBtn" class="p-2 bg-slate-100 rounded-full text-slate-500"><i data-lucide="lock" size="20"></i></button>
        </div>
    </header>

    <main id="app" class="max-w-2xl mx-auto px-4 py-6">
        <div id="view-container" class="slide-up"></div>
    </main>

    <nav class="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 py-3 flex justify-around shadow-sm">
        <button onclick="switchTab('poll')" class="nav-item flex flex-col items-center gap-1 text-indigo-600" id="nav-poll">
            <i data-lucide="star"></i><span class="text-[10px] font-bold uppercase">Rate</span>
        </button>
        <button onclick="switchTab('results')" class="nav-item flex flex-col items-center gap-1 text-slate-400" id="nav-results">
            <i data-lucide="bar-chart-2"></i><span class="text-[10px] font-bold uppercase">Rank</span>
        </button>
        <button onclick="switchTab('teams')" class="nav-item flex flex-col items-center gap-1 text-slate-400" id="nav-teams">
            <i data-lucide="users"></i><span class="text-[10px] font-bold uppercase">Teams</span>
        </button>
    </nav>

    <div id="loginModal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 hidden items-center justify-center p-4">
        <div class="bg-white w-full max-w-sm rounded-3xl p-8 space-y-6">
            <div class="flex justify-between items-start">
                <div class="p-3 bg-indigo-50 text-indigo-600 rounded-2xl"><i data-lucide="lock"></i></div>
                <button onclick="toggleModal('loginModal', false)"><i data-lucide="x"></i></button>
            </div>
            <div>
                <h3 class="text-xl font-bold">Admin Panel</h3>
                <p class="text-slate-500 text-sm">Add or remove players from the list.</p>
            </div>
            <input type="password" id="adminPassword" placeholder="Password" class="w-full px-4 py-4 bg-slate-50 border rounded-2xl outline-none focus:ring-2 focus:ring-indigo-500">
            <button onclick="handleAdminLogin()" class="w-full py-4 bg-indigo-600 text-white font-bold rounded-2xl">Unlock</button>
        </div>
    </div>

    <script>
        let state = { players: [], submissions: {}, voterId: null, myVote: null, activeTab: 'poll', currentPollIndex: 0, tempRatings: {}, isAdmin: false, isEditing: false };

        async function fetchData() {
            const res = await fetch('/api/data');
            const data = await res.json();
            state.players = data.players;
            state.submissions = data.submissions;
            state.voterId = data.voter_id;
            state.myVote = data.my_vote;
            if (state.myVote && !state.isEditing) state.tempRatings = { ...state.myVote };
            else state.players.forEach(p => { if (!state.tempRatings[p.name]) state.tempRatings[p.name] = 5; });
            render();
        }

        function switchTab(tab) {
            state.activeTab = tab;
            document.querySelectorAll('.nav-item').forEach(el => el.classList.replace('text-indigo-600', 'text-slate-400'));
            const target = document.getElementById(`nav-${tab}`);
            if(target) target.classList.replace('text-slate-400', 'text-indigo-600');
            render();
        }

        function toggleModal(id, show) {
            const el = document.getElementById(id);
            el.classList.toggle('hidden', !show);
            el.classList.toggle('flex', show);
        }

        async function handleAdminLogin() {
            const password = document.getElementById('adminPassword').value;
            const res = await fetch('/api/admin/login', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ password }) });
            if (res.ok) { state.isAdmin = true; toggleModal('loginModal', false); switchTab('admin'); } else alert("Access Denied");
        }

        async function identifyPlayer(playerId) {
            if(!playerId) return;
            const res = await fetch('/api/identify', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ player_id: playerId }) });
            if (res.ok) fetchData();
        }

        async function submitPoll() {
            await fetch('/api/vote', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ ratings: state.tempRatings }) });
            state.isEditing = false; fetchData();
        }

        async function addPlayer(name) {
            if (!name) return;
            await fetch('/api/admin/players', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ name }) });
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
                if (!state.voterId) {
                    container.innerHTML = `
                        <div class="bg-white p-8 rounded-3xl shadow-sm border border-slate-100 text-center space-y-6">
                            <h2 class="text-2xl font-bold">Player Identity</h2>
                            <p class="text-slate-500 text-sm">Select your name to begin voting.</p>
                            ${state.players.length > 0 ? `
                                <select id="playerSelect" class="w-full px-4 py-4 bg-slate-50 border rounded-2xl outline-none focus:ring-2 focus:ring-indigo-500 appearance-none">
                                    <option value="" disabled selected>Choose your name...</option>
                                    ${state.players.map(p => `<option value="${p.id}">${p.name} ${state.submissions[p.id] ? '✓' : ''}</option>`).join('')}
                                </select>
                                <button onclick="identifyPlayer(document.getElementById('playerSelect').value)" class="w-full py-4 bg-indigo-600 text-white font-bold rounded-2xl">Start Voting</button>
                            ` : `<p class="text-orange-500 text-sm font-medium">The player list is currently empty. Please wait for the admin to add players.</p>`}
                        </div>
                    `;
                } else if (state.myVote && !state.isEditing) {
                    container.innerHTML = `
                        <div class="text-center py-12 space-y-6">
                            <div class="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto"><i data-lucide="check" size="40"></i></div>
                            <div>
                                <h2 class="text-2xl font-bold">Submission Received</h2>
                                <p class="text-slate-500 text-sm mt-1">Logged in as: <b>${state.players.find(p=>p.id===state.voterId)?.name}</b></p>
                            </div>
                            <div class="flex flex-col gap-3">
                                <button onclick="state.isEditing=true; render();" class="bg-indigo-600 text-white py-4 rounded-2xl font-bold shadow-lg">Edit My Ratings</button>
                                <button onclick="state.voterId=null; render();" class="text-slate-400 text-xs font-bold">Log out / Change Identity</button>
                            </div>
                        </div>
                    `;
                } else if (state.players.length > 0) {
                    const p = state.players[state.currentPollIndex];
                    const progress = Math.round(((state.currentPollIndex + 1) / state.players.length) * 100);
                    container.innerHTML = `
                        <div class="bg-white p-6 rounded-3xl border border-slate-100 space-y-8">
                            <div class="flex justify-between items-center text-xs font-bold uppercase text-slate-400 tracking-widest">
                                <span>Player ${state.currentPollIndex + 1} of ${state.players.length}</span>
                                <span class="text-indigo-600">${progress}%</span>
                            </div>
                            <div class="flex items-center gap-4">
                                <div class="w-16 h-16 bg-indigo-600 rounded-2xl flex items-center justify-center text-white text-2xl font-bold">${p.name[0]}</div>
                                <div>
                                    <h2 class="text-2xl font-bold">${p.name}</h2>
                                    <p class="text-slate-400 text-sm">Rating: <span class="text-indigo-600 font-bold">${state.tempRatings[p.name] || 5}</span>/10</p>
                                </div>
                            </div>
                            <input type="range" min="1" max="10" value="${state.tempRatings[p.name] || 5}" oninput="state.tempRatings['${p.name}']=this.value; render();" class="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer">
                            <div class="flex gap-3">
                                ${state.currentPollIndex > 0 ? `<button onclick="state.currentPollIndex--; render();" class="flex-1 py-4 bg-slate-100 font-bold rounded-2xl">Back</button>` : ''}
                                ${state.currentPollIndex < state.players.length - 1 ? `<button onclick="state.currentPollIndex++; render();" class="flex-[2] py-4 bg-indigo-600 text-white font-bold rounded-2xl shadow-lg">Next</button>` : `<button onclick="submitPoll()" class="flex-[2] py-4 bg-green-600 text-white font-bold rounded-2xl">Save All</button>`}
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
                    <div class="bg-white p-6 rounded-3xl border border-slate-100">
                        <div class="flex justify-between items-center mb-8">
                            <h2 class="text-xl font-bold">Leaderboard</h2>
                            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">${Object.keys(state.submissions).length} Voters</span>
                        </div>
                        <div class="space-y-6">
                            ${leaderboard.map((p, i) => `
                                <div class="flex items-center gap-4">
                                    <span class="w-6 text-sm font-bold text-slate-300">${i+1}</span>
                                    <div class="flex-1">
                                        <div class="flex justify-between mb-1 text-sm">
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
            } else if (state.activeTab === 'teams') {
                const leaderboard = state.players.map(p => {
                    const scores = Object.values(state.submissions).map(s => s[p.name]).filter(v => v !== undefined);
                    const avg = scores.length ? (scores.reduce((a,b)=>a+parseInt(b),0) / scores.length).toFixed(1) : 0;
                    return { name: p.name, avg: parseFloat(avg) };
                }).sort((a,b) => b.avg - a.avg);

                const teamA = [];
                const teamB = [];

                leaderboard.forEach((player, index) => {
                    if (index % 2 === 0) teamA.push(player);
                    else teamB.push(player);
                });

                container.innerHTML = `
                    <div class="space-y-6">
                        <div class="bg-white p-6 rounded-3xl border border-slate-100">
                            <h2 class="text-xl font-bold mb-2">Balanced Teams</h2>
                            <p class="text-slate-500 text-sm mb-6">Split based on alternating ranking positions to balance skill level.</p>
                            
                            <div class="grid grid-cols-2 gap-4">
                                <!-- Team A -->
                                <div class="space-y-4">
                                    <div class="flex items-center gap-2 mb-2">
                                        <div class="w-2 h-2 rounded-full bg-indigo-500"></div>
                                        <h3 class="font-bold text-xs uppercase tracking-widest text-slate-400">Team A</h3>
                                    </div>
                                    <div class="space-y-2">
                                        ${teamA.map(p => `
                                            <div class="p-3 bg-slate-50 rounded-xl text-sm font-medium border border-slate-100 flex flex-col gap-1">
                                                <span class="truncate">${p.name}</span>
                                                <span class="text-[10px] text-slate-400 font-bold">${p.avg}</span>
                                            </div>
                                        `).join('')}
                                        ${teamA.length === 0 ? '<p class="text-xs text-slate-300 italic">No players</p>' : ''}
                                    </div>
                                </div>

                                <!-- Team B -->
                                <div class="space-y-4">
                                    <div class="flex items-center gap-2 mb-2">
                                        <div class="w-2 h-2 rounded-full bg-emerald-500"></div>
                                        <h3 class="font-bold text-xs uppercase tracking-widest text-slate-400">Team B</h3>
                                    </div>
                                    <div class="space-y-2">
                                        ${teamB.map(p => `
                                            <div class="p-3 bg-slate-50 rounded-xl text-sm font-medium border border-slate-100 flex flex-col gap-1">
                                                <span class="truncate">${p.name}</span>
                                                <span class="text-[10px] text-slate-400 font-bold">${p.avg}</span>
                                            </div>
                                        `).join('')}
                                        ${teamB.length === 0 ? '<p class="text-xs text-slate-300 italic">No players</p>' : ''}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            } else if (state.activeTab === 'admin') {
                container.innerHTML = `
                    <div class="bg-white p-6 rounded-3xl border border-slate-100 space-y-8">
                        <div class="flex justify-between items-center">
                            <h2 class="text-xl font-bold">Manage Roster</h2>
                            <button onclick="state.isAdmin=false; switchTab('poll');" class="text-xs text-red-500 font-bold">Exit</button>
                        </div>
                        <div class="flex gap-2">
                            <input type="text" id="newName" placeholder="Player Name" class="flex-1 px-4 py-3 bg-slate-50 border rounded-xl outline-none focus:ring-2 focus:ring-indigo-500">
                            <button onclick="addPlayer(document.getElementById('newName').value)" class="p-3 bg-indigo-600 text-white rounded-xl"><i data-lucide="plus"></i></button>
                        </div>
                        <div class="space-y-2">
                            ${state.players.length === 0 ? `<p class="text-center text-slate-300 text-sm py-4 italic">No players added yet.</p>` : state.players.map(p => `
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

        document.getElementById('adminBtn').onclick = () => state.isAdmin ? switchTab('admin') : toggleModal('loginModal', true);
        window.onload = fetchData;
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)