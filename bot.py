import discord
import json
from discord.ext import commands
from discord import app_commands
import time
import os

TOKEN = os.getenv("token")
ADMIN_CHANNEL_ID = 1350681415095816255
STOCK_FILE = "stock.json"
SOURCE_FILE = "source.json"
LEGIT_FILE = "legit.json"
BUYER_ROLE_ID = 1340669678951071827
ADMIN_ID = 1219200091777269792

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

bot.transaction_data = {}

def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

class StockSelect(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.update_options()

    def update_options(self):
        stock_data = load_json(STOCK_FILE)
        self.clear_items()
        options = [
            discord.SelectOption(label=item, description=f"Còn {quantity} cái", value=item)
            for item, quantity in stock_data.items()
        ]
        self.select = discord.ui.Select(placeholder="Chọn sản phẩm để kiểm tra", options=options)
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: discord.Interaction):
        stock_data = load_json(STOCK_FILE)
        product = self.select.values[0]
        quantity = stock_data.get(product, 0)

        embed = discord.Embed(
            title="📦 Kiểm Tra Stock",
            description=f"🔹 **{product}**: Còn `{quantity}` cái trong kho.",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=self)

@bot.tree.command(name="stock", description="Kiểm tra số lượng hàng trong kho.")
async def stock(interaction: discord.Interaction):
    await interaction.response.send_message("📋 **Chọn sản phẩm để kiểm tra stock:**", view=StockSelect(), ephemeral=True)

@bot.tree.command(name="update_stock", description="Cập nhật số lượng hàng hóa trong kho (Admin).")
@app_commands.describe(product="Tên sản phẩm", quantity="Số lượng mới")
async def update_stock(interaction: discord.Interaction, product: str, quantity: int):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("⛔ Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
        return
    
    if quantity < 0:
        await interaction.response.send_message("⚠ Số lượng không hợp lệ!", ephemeral=True)
        return
    
    stock_data = load_json(STOCK_FILE)
    stock_data[product] = quantity
    save_json(STOCK_FILE, stock_data)

    embed = discord.Embed(
        title="✅ Cập Nhật Stock Thành Công!",
        description=f"🔹 **{product}**: Còn `{quantity}` cái trong kho.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="delete_stock", description="Xóa sản phẩm khỏi kho (Admin).")
@app_commands.describe(product="Tên sản phẩm cần xóa")
async def delete_stock(interaction: discord.Interaction, product: str):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("⛔ Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
        return

    stock_data = load_json(STOCK_FILE)

    if product not in stock_data:
        await interaction.response.send_message(f"⚠ **Sản phẩm `{product}` không có trong kho!**", ephemeral=True)
        return

    del stock_data[product]
    save_json(STOCK_FILE, stock_data)

    embed = discord.Embed(
        title="🗑️ Xóa Sản Phẩm Thành Công!",
        description=f"🔹 **{product}** đã được **xóa khỏi kho**.",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

class SourceSelect(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.update_options()

    def update_options(self):
        source_data = load_json(SOURCE_FILE)
        self.clear_items()
        options = [
            discord.SelectOption(label=item, description=f"Còn {quantity} cái", value=item, emoji="📦")
            for item, quantity in source_data.items()
        ]
        self.select = discord.ui.Select(placeholder="Chọn source để kiểm tra", options=options)
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: discord.Interaction):
        source_data = load_json(SOURCE_FILE)
        product = self.select.values[0]
        quantity = source_data.get(product, 0)

        embed = discord.Embed(
            title="📦 Kiểm Tra Source",
            description=f"🔹 **{product}**: Còn `{quantity}` cái trong kho.",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=self)

@bot.tree.command(name="source", description="Kiểm tra số lượng source có sẵn.")
async def source(interaction: discord.Interaction):
    await interaction.response.send_message("📋 **Chọn source để kiểm tra:**", view=SourceSelect(), ephemeral=True)

@bot.tree.command(name="update_source", description="Cập nhật số lượng source (Admin).")
@app_commands.describe(product="Tên source", quantity="Số lượng mới")
async def update_source(interaction: discord.Interaction, product: str, quantity: int):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("⛔ Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
        return
    
    if quantity < 0:
        await interaction.response.send_message("⚠ Số lượng không hợp lệ!", ephemeral=True)
        return
    
    source_data = load_json(SOURCE_FILE)
    source_data[product] = quantity
    save_json(SOURCE_FILE, source_data)

    embed = discord.Embed(
        title="✅ Cập Nhật Source Thành Công!",
        description=f"🔹 **{product}**: Còn `{quantity}` cái trong kho.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'✅ Bot {bot.user} đã sẵn sàng!')

bot.run(TOKEN)
