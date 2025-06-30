import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from flask import Flask, render_template
import threading

# .envの読み込み
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CASH_CHANNEL_ID = int(os.getenv("CASH_CHANNEL_ID"))
ALLOWED_USERS = [1376293325635850374]  # 許可ユーザーID

# 権限チェック用関数
def is_allowed(interaction: discord.Interaction):
    return interaction.user.id in ALLOWED_USERS

# Botクラス
class LTCBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ スラッシュコマンド同期完了")

bot = LTCBot()

# Flask app
app = Flask(__name__)

@app.route('/')
def home():
    if bot.is_ready():
        status = "Bot is online"
        color = "green"
    else:
        status = "Bot is offline"
        color = "red"
    return render_template('index.html', status=status, color=color, bot_name=bot.user.name if bot.user else "LTC Bot")

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

# モーダル申請フォーム
class CashModal(discord.ui.Modal, title="LTC自動換金"):
    amount = discord.ui.TextInput(label="LTC金額", placeholder="例: 0.01", required=True)
    ltc_address = discord.ui.TextInput(label="LTCアドレス", placeholder="LTCアドレス", required=True)
    paypay_link = discord.ui.TextInput(label="PayPayリンク", placeholder="https://pay.paypay", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        channel = bot.get_channel(CASH_CHANNEL_ID)
        embed = discord.Embed(title="💰換金", color=0x00cc99)
        embed.add_field(name="換金者", value=interaction.user.mention, inline=False)
        embed.add_field(name="金額", value=f"{self.amount.value} LTC", inline=False)
        embed.add_field(name="LTCアドレス", value=self.ltc_address.value, inline=False)
        embed.add_field(name="PayPayリンク", value=self.paypay_link.value, inline=False)

        await channel.send(embed=embed)
        await interaction.response.send_message("✅ 申請を送信しました。", ephemeral=True)

# パネル用ボタン
class CashPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="換金する", style=discord.ButtonStyle.green, custom_id="cash_button")
    async def cash_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CashModal())

# パネル設置コマンド
@bot.tree.command(name="setup_cash_panel", description="換金パネルを設置します（管理者専用）")
async def setup_panel(interaction: discord.Interaction):
    if not is_allowed(interaction):
        await interaction.response.send_message("❌ 許可されたユーザーのみ使用できます。", ephemeral=True)
        return

    embed = discord.Embed(title="LTC換金はこちら", description="以下のボタンを押して入力してください。", color=0x3399ff)
    await interaction.channel.send(embed=embed, view=CashPanel())
    await interaction.response.send_message("✅ パネルを設置しました。", ephemeral=True)

# 偽換金ログ送信コマンド（LTC）
@bot.tree.command(name="connect_paypay", description="PayPayを連携します（管理者専用）")
@app_commands.describe(
    user="偽の申請者名（@mentionでもOK）",
    amount="LTC金額",
    channel_id="送信先チャンネルID（IDで入力）"
)
async def send_fake_log(interaction: discord.Interaction, user: str, amount: str, channel_id: str):
    if not is_allowed(interaction):
        await interaction.response.send_message("❌ 許可されたユーザーのみ使用できます。", ephemeral=True)
        return
    try:
        channel = await bot.fetch_channel(int(channel_id))
    except Exception as e:
        await interaction.response.send_message(f"❌ チャンネル取得に失敗: {e}", ephemeral=True)
        return

    embed = discord.Embed(title="🪙 換金ログ", color=0xff9933)
    embed.add_field(name="👤 換金者", value=user, inline=False)
    embed.add_field(name="💰 金額", value=f"{amount} LTC", inline=False)
    embed.set_footer(text="よかったらまた買ってください")

    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ 偽ログを {channel.mention} に送信しました。", ephemeral=True)

# 偽実績送信コマンド
@bot.tree.command(name="stake_cooperation", description="stakeと連携します（管理者専用）")
@app_commands.describe(
    user="対象ユーザー（名前や@mention）",
    title="実績タイトル",
    rating="評価（1〜5）",
    count="回数または個数"
)
async def fake_achievement(interaction: discord.Interaction, user: str, title: str,
                           rating: app_commands.Range[int, 1, 5], count: int):
    if not is_allowed(interaction):
        await interaction.response.send_message("❌ 許可されたユーザーのみ使用できます。", ephemeral=True)
        return

    stars = "★" * rating
    embed = discord.Embed(title="📦 実績報告", color=0xf1c40f)
    embed.add_field(name="👤 記入者", value=user, inline=False)
    embed.add_field(name="🛒 商品名", value=title, inline=False)
    embed.add_field(name="✨ 評価", value=stars, inline=False)
    embed.add_field(name="💰 個数", value=f"{count} 回", inline=False)
    embed.set_footer(text="よかったら買ってください")

    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("✅ 偽実績を送信しました。", ephemeral=True)

# Bot起動時
@bot.event
async def on_ready():
    bot.add_view(CashPanel())  # Viewの永続登録
    print(f"🟢 Bot起動完了: {bot.user}")

# Flask サーバーを別スレッドで起動
flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# 実行
bot.run(TOKEN)
