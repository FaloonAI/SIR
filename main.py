from telethon import TelegramClient, errors
import asyncio
import typer
from rich.console import Console
from rich.progress import Progress
import os
from dotenv import load_dotenv
import signal

# Загружаем переменные окружения
load_dotenv()

app = typer.Typer()
console = Console()
paused = False

# Функция для создания клиента
def create_client(session_name, app_id, app_hash):
    return TelegramClient(session_name, app_id, app_hash)

def toggle_pause(signum, frame):
    global paused
    paused = not paused
    console.print("[yellow]Пауза[/yellow]" if paused else "[green]Продолжение[/green]")

@app.command()
def main():
    signal.signal(signal.SIGINT, toggle_pause)  # Ctrl+C для паузы
    console.print("""
  ____ ___ ____    _             _____ _    _     ___   ___  _   _ 
 / ___|_ _|  _ \  | |__  _   _  |  ___/ \  | |   / _ \ / _ \| \ | |
 \___ \| || |_) | | '_ \| | | | | |_ / _ \ | |  | | | | | | |  \| |
  ___) | ||  _ <  | |_) | |_| | |  _/ ___ \| |__| |_| | |_| | |\  |
 |____/___|_| \_\ |_.__/ \__, | |_|/_/   \_\_____\___/ \___/|_| \_|
                         |___/                                     
    """)
    mode = typer.prompt("Выберите режим (New/Old)", default="old")

    if mode == "new":
        app_id = int(typer.prompt("Введите App ID"))
        app_hash = typer.prompt("Введите App Hash")
    else:
        app_id = int(os.getenv("APP_ID", "12345"))
        app_hash = os.getenv("APP_HASH")

    bot_link = typer.prompt("Введите ссылку на бота (t.me/...)")
    message = typer.prompt("Введите сообщение для отправки")
    cycles = int(typer.prompt("Сколько циклов отправить?", default="1"))
    
    client = create_client("anon_bot_session", app_id, app_hash)

    async def send_message_to_bot():
        await client.start()
        console.print("[green]Клиент успешно запущен![/green]")

        bot_username = bot_link.split('t.me/')[-1].split('?')[0]
        start_param = bot_link.split('start=')[-1] if 'start=' in bot_link else None

        with Progress(transient=True) as progress:
            task = progress.add_task("[cyan]Отправка сообщений...[/cyan]", total=cycles)

            for i in range(cycles):
                while paused:
                    await asyncio.sleep(1)  # Ждём, пока пауза не будет снята

                try:
                    if start_param:
                        await client.send_message(bot_username, f"/start {start_param}")
                        console.print(f"[blue]Перешли по ссылке: /start {start_param}[/blue]")

                    await client.send_message(bot_username, message)
                    console.print(f"[green]Сообщение отправлено: {message}[/green]")
                    progress.update(task, advance=1)
                except errors.FloodWaitError as e:
                    console.print(f"[red]Обнаружена задержка: {e.seconds} секунд[/red]")
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    console.print(f"[red]Ошибка: {e}[/red]")
                    break

        await client.disconnect()
        console.print("[bold magenta]Клиент отключён.[/bold magenta]")

    with client:
        client.loop.run_until_complete(send_message_to_bot())

if __name__ == "__main__":
    app()
