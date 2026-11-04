from warnect import BaileysClient

client = BaileysClient(auth_dir="auth")

def on_qr(qr):
    print("SCAN QR INI:")
    print(qr)

def on_connection(state):
    print("Connection:", state)

def on_message(msg):
    text = msg.get("text")
    jid = (msg.get("key") or {}).get("remoteJid")
    print("Pesan masuk:", text)
    if text and jid:
        client.send_text(jid, f"Echo: {text}")

client.on("qr", on_qr)
client.on("connection", on_connection)
client.on("message", on_message)

client.start()
input("Bot jalan. Tekan Enter untuk stop...\n")
client.stop()
