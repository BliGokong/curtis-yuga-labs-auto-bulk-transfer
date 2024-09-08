import random
import time
from web3 import Web3
import logging
from dotenv import load_dotenv
import os
from datetime import datetime

# Memuat variabel lingkungan dari .env
load_dotenv()

# Mendapatkan informasi akun pengirim dari .env
sender_address = os.getenv("SENDER_ADDRESS")
private_key = os.getenv("PRIVATE_KEY")

# Koneksi ke Curtis RPC
rpc_url = "https://curtis.rpc.caldera.xyz/http"
web3 = Web3(Web3.HTTPProvider(rpc_url))

# Chain ID Curtis
chain_id = 33111

# Konfigurasi logging
logging.basicConfig(filename='bulk_transfer.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s: %(message)s')

# Warna untuk terminal
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
TIMESTAMP_GREEN = "\033[92m"
TIMESTAMP_RED = "\033[91m"

# Fungsi untuk membaca alamat dari file
def read_recipients(file_path):
    try:
        with open(file_path, 'r') as file:
            addresses = [line.strip() for line in file if line.strip()]
        random.shuffle(addresses)  # Mengacak daftar penerima
        logging.info(f"Berhasil memuat dan mengacak {len(addresses)} alamat penerima.")
        return addresses
    except Exception as e:
        logging.error(f"Gagal memuat file penerima. Kesalahan: {str(e)}")
        return []

# Fungsi untuk mengecek saldo
def check_balance(sender):
    balance = web3.eth.get_balance(sender)
    logging.info(f'Saldo akun pengirim: {web3.from_wei(balance, "ether")} APE')
    return balance

# Fungsi untuk validasi saldo
def validate_balance(sender, total_amount):
    balance = check_balance(sender)
    
    # Hitung total yang akan dikirim + biaya gas
    total_required = total_amount + web3.to_wei(0.001, 'ether')  # Estimasi gas
    if balance < total_required:
        logging.error("Saldo tidak mencukupi untuk transfer.")
        return False
    return True

# Fungsi untuk membuat random amount (0.01 + random(11-99))
def generate_random_amount():
    random_number = random.randint(11, 99)  # Menghasilkan angka acak antara 11 dan 99
    amount = 0.01 + (random_number / 10000)  # Menghitung jumlah transfer
    return web3.to_wei(amount, 'ether'), amount  # Mengembalikan amount dalam wei dan ether

# Fungsi untuk melakukan transfer
def send_bulk_transactions(sender, private_key, recipients):
    nonce = web3.eth.get_transaction_count(sender)
    processed_recipients = set()  # Set untuk melacak penerima yang sudah diproses

    total_amount = 0
    transactions = []

    for address in recipients:
        if address in processed_recipients:
            continue
        amount_in_wei, amount_in_ether = generate_random_amount()
        total_amount += amount_in_wei
        transactions.append({"address": address, "amount": amount_in_wei, "amount_ether": amount_in_ether})
        processed_recipients.add(address)  # Tambah ke set penerima yang sudah diproses

    if not validate_balance(sender, total_amount):
        print("Saldo tidak mencukupi, menghentikan proses.")
        return

    for recipient in transactions:
        try:
            transaction = {
                'to': recipient['address'],
                'value': recipient['amount'],
                'gas': 21000,  # Estimasi gas
                'gasPrice': web3.to_wei('5', 'gwei'),
                'nonce': nonce,
                'chainId': chain_id
            }

            # Tanda tangani transaksi
            signed_txn = web3.eth.account.sign_transaction(transaction, private_key)

            # Kirim transaksi
            tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

            # Ambil timestamp saat ini
            timestamp = datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")

            # Tampilkan pesan dengan timestamp dan warna hijau
            print(f"{TIMESTAMP_GREEN}{timestamp}{RESET} {GREEN}Transaksi berhasil dikirim ke {recipient['address']}. Hash: {web3.to_hex(tx_hash)}. Jumlah: {recipient['amount_ether']} APE{RESET}")
            logging.info(f"Transaksi dikirim ke {recipient['address']}. Hash: {web3.to_hex(tx_hash)}. Jumlah: {recipient['amount_ether']} APE")

            # Jeda acak antara 15 detik hingga 2 menit
            wait_time = random.randint(15, 120)  # Menghasilkan waktu jeda acak dalam detik
            print(f"Menunggu {wait_time} detik sebelum transaksi berikutnya...")
            logging.info(f"Menunggu {wait_time} detik sebelum transaksi berikutnya...")
            time.sleep(wait_time)

            # Update nonce untuk transaksi berikutnya
            nonce += 1

        except Exception as e:
            logging.error(f"Gagal mengirim transaksi ke {recipient['address']}. Kesalahan: {str(e)}")
            # Ambil timestamp saat ini
            timestamp = datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")
            # Tampilkan pesan dengan timestamp dan warna merah
            print(f"{TIMESTAMP_RED}{timestamp}{RESET} {RED}Gagal mengirim transaksi ke {recipient['address']}. Lihat log untuk detailnya.{RESET}")

# Membaca alamat penerima dari file
recipients = read_recipients('recipients.txt')

# Eksekusi bulk transfer jika ada penerima
if recipients:
    send_bulk_transactions(sender_address, private_key, recipients)
else:
    print("Tidak ada penerima yang ditemukan.")
