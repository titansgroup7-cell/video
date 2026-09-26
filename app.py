from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'badilisha-siri-hii')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# room_id -> list of {sid, username}
rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create')
def create():
    room_id = str(uuid.uuid4())[:8]
    return render_template('room.html', room_id=room_id)

@app.route('/room/<room_id>')
def room(room_id):
    return render_template('room.html', room_id=room_id)

@socketio.on('join')
def on_join(data):
    room = data['room']
    username = data.get('username', f'User-{request.sid[:5]}')
    join_room(room)

    if room not in rooms:
        rooms[room] = []

    # Avoid duplicates
    rooms[room] = [u for u in rooms[room] if u['sid'] != request.sid]
    rooms[room].append({'sid': request.sid, 'username': username})

    # Tuma list kamili kwa mpya
    emit('user-list', {'users': rooms[room]}, room=request.sid)

    # Arifu wengine
    emit('user-joined', {
        'sid': request.sid,
        'username': username
    }, room=room, include_self=False)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] {username} joined {room}")

@socketio.on('offer')
def on_offer(data):
    emit('offer', data, room=data['target'])

@socketio.on('answer')
def on_answer(data):
    emit('answer', data, room=data['target'])

@socketio.on('ice-candidate')
def on_ice(data):
    emit('ice-candidate', data, room=data['target'])

@socketio.on('chat-message')
def on_chat(data):
    room = data['room']
    emit('chat-message', {
        'username': data['username'],
        'message': data['message'],
        'time': datetime.now().strftime('%H:%M')
    }, room=room)

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    for room, users in list(rooms.items()):
        for user in users[:]:
            if user['sid'] == sid:
                username = user['username']
                users.remove(user)
                emit('user-left', {'sid': sid, 'username': username}, room=room)
                if not users:
                    del rooms[room]
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {username} left {room}")
                break

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
