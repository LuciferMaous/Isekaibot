import discord
import json
from discord.ext import commands
from discord import app_commands
import time
import os

TOKEN = os.getenv("token")  # Lấy TOKEN từ biến môi trường
ADMIN_CHANNEL_ID = 1350681415095816255  # Thay bằng ID kênh Discord admin để bot gửi tin nhắn
STOCK_FILE = "stock.json"
LEGIT_FILE = "legit.json"
BUYER_ROLE_ID = 1340669678951071827
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionary để lưu thông tin giao dịch
bot.transaction_data = {}

class NapThe(discord.ui.Modal, title="Nạp Thẻ Cào"):
    loai = discord.ui.TextInput(label="Loại thẻ (Viettel, Vinaphone, Mobifone)", required=True)
    menhgia = discord.ui.TextInput(label="Mệnh giá (VD: 100000)", required=True)
    mathe = discord.ui.TextInput(label="Mã thẻ", required=True)
    seri = discord.ui.TextInput(label="Số seri", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)

        if admin_channel:
            embed = discord.Embed(
                title="📩 Yêu Cầu Nạp Thẻ",
                description=f"**Người gửi:** {interaction.user.mention}\n"
                            f"**Loại thẻ:** {self.loai.value}\n"
                            f"**Mệnh giá:** {self.menhgia.value} VNĐ\n"
                            f"**Mã thẻ:** `{self.mathe.value}`\n"
                            f"**Số seri:** `{self.seri.value}`",
                color=discord.Color.blue()
            )
            await admin_channel.send(embed=embed)
            await interaction.response.send_message("✅ **Thông tin thẻ đã được gửi đến admin!** Vui lòng chờ xử lý.", ephemeral=True)
        else:
            await interaction.response.send_message("⚠ **Không tìm thấy kênh admin để gửi tin nhắn!**", ephemeral=True)

class ChuyenKhoan(discord.ui.Modal, title="Chuyển Khoản Ngân Hàng"):
    bank_name = discord.ui.TextInput(label="Tên ngân hàng (VD: Vietcombank, Momo, MB)", required=True)
    amount = discord.ui.TextInput(label="Số tiền (VD: 200000)", required=True)
    trans_id = discord.ui.TextInput(label="Mã giao dịch", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
            if not admin_channel:
                await interaction.response.send_message("⚠ **Không tìm thấy kênh admin để gửi tin nhắn!**", ephemeral=True)
                return
            
            # Gửi tin nhắn hướng dẫn user gửi ảnh xác nhận
            msg = await interaction.channel.send(
                f"{interaction.user.mention} ✅ **Thông tin đã được ghi nhận!** "
                "Vui lòng gửi ảnh hóa đơn giao dịch bằng cách **reply** tin nhắn này với ảnh của bạn."
            )

            # Lưu ID tin nhắn bot gửi để kiểm tra reply sau này
            bot.transaction_data[interaction.user.id] = {
                "user": interaction.user.mention,
                "bank": self.bank_name.value,
                "amount": self.amount.value,
                "trans_id": self.trans_id.value,
                "msg_id": msg.id  # Lưu ID tin nhắn này
            }

            await interaction.response.send_message("✅ **Thông tin đã được ghi nhận!** Vui lòng gửi ảnh xác nhận.", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ **Đã xảy ra lỗi:** {str(e)}", ephemeral=True)


@bot.tree.command(name="bank", description="Nạp tiền qua ngân hàng, yêu cầu gửi ảnh hóa đơn giao dịch.")
async def bank(interaction: discord.Interaction):
    await interaction.response.send_modal(ChuyenKhoan())

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id in bot.transaction_data and message.attachments:
        admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
        data = bot.transaction_data.pop(message.author.id)  # Lấy thông tin giao dịch

        embed = discord.Embed(
            title="📩 Yêu Cầu Chuyển Khoản",
            description=f"**Người gửi:** {data['user']}\n"
                        f"**Ngân hàng:** {data['bank']}\n"
                        f"**Số tiền:** {data['amount']} VNĐ\n"
                        f"**Mã giao dịch:** `{data['trans_id']}`",
            color=discord.Color.green()
        )

        if admin_channel:
            # Gửi thông tin giao dịch trước
            await admin_channel.send(embed=embed)

            for attachment in message.attachments:
                # Tạo embed chứa ảnh
                image_embed = discord.Embed(
                    title="📸 Ảnh Giao Dịch",
                    color=discord.Color.blue()
                )
                image_embed.set_image(url=attachment.url)

                # Gửi embed ảnh lên admin
                await admin_channel.send(embed=image_embed)
            
            # Xóa tin nhắn người dùng và tin nhắn bot trước đó
            time.sleep(5)
            await message.delete()
            try:
                msg = await message.channel.fetch_message(data["msg_id"])  # Lấy tin nhắn bot đã gửi
                await msg.delete()
            except discord.NotFound:
                pass  # Nếu tin nhắn bot không còn, bỏ qua lỗi

            await message.channel.send("✅ **Ảnh đã được gửi lên admin!** Vui lòng chờ xác nhận.", delete_after=5)
        else:
            await message.channel.send("⚠ **Không tìm thấy kênh admin để gửi tin nhắn!**", delete_after=5)


# Hàm tải dữ liệu stock từ file (luôn cập nhật mỗi lần lệnh được dùng)
def load_stock():
    try:
        with open(STOCK_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # Trả về dict rỗng nếu file lỗi

# Hàm lưu stock vào file
def save_stock(stock_data):
    with open(STOCK_FILE, "w", encoding="utf-8") as file:
        json.dump(stock_data, file, indent=4, ensure_ascii=False)

class StockSelect(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)  # Hết hạn sau 60s
        self.update_options()

    def update_options(self):
        stock_data = load_stock()  # Load dữ liệu mới nhất
        self.clear_items()
        options = [
            discord.SelectOption(label=item, description=f"Còn {quantity} cái", value=item)
            for item, quantity in stock_data.items()
        ]
        self.select = discord.ui.Select(placeholder="Chọn sản phẩm để kiểm tra", options=options)
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: discord.Interaction):
        stock_data = load_stock()  # Load lại stock mới nhất
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
ADMIN_ID = 1219200091777269792  # Thay bằng ID Discord của bạn

@bot.tree.command(name="update_stock", description="Cập nhật số lượng hàng hóa trong kho (Admin).")
@app_commands.describe(product="Tên sản phẩm", quantity="Số lượng mới")
async def update_stock(interaction: discord.Interaction, product: str, quantity: int):
    if interaction.user.id != ADMIN_ID:  # Kiểm tra nếu không phải admin
        await interaction.response.send_message("⛔ **Bạn không có quyền sử dụng lệnh này!**", ephemeral=True)
        return

    if quantity < 0:
        await interaction.response.send_message("⚠ Số lượng không hợp lệ!", ephemeral=True)
        return
    
    stock_data = load_stock()
    stock_data[product] = quantity
    save_stock(stock_data)

    embed = discord.Embed(
        title="✅ Cập Nhật Stock Thành Công!",
        description=f"🔹 **{product}**: Còn `{quantity}` cái trong kho.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="delete_stock", description="Xóa sản phẩm khỏi kho (Admin).")
@app_commands.describe(product="Tên sản phẩm cần xóa")
async def delete_stock(interaction: discord.Interaction, product: str):
    if interaction.user.id != ADMIN_ID:  # Kiểm tra quyền admin
        await interaction.response.send_message("⛔ **Bạn không có quyền sử dụng lệnh này!**", ephemeral=True)
        return

    stock_data = load_stock()

    if product not in stock_data:
        await interaction.response.send_message(f"⚠ **Sản phẩm `{product}` không có trong kho!**", ephemeral=True)
        return

    del stock_data[product]  # Xóa sản phẩm khỏi dictionary
    save_stock(stock_data)  # Lưu lại dữ liệu

    embed = discord.Embed(
        title="🗑️ Xóa Sản Phẩm Thành Công!",
        description=f"🔹 **{product}** đã được **xóa khỏi kho**.",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Hàm tải dữ liệu legit từ file
def load_legit():
    try:
        with open(LEGIT_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"store": 0}

# Hàm lưu dữ liệu legit vào file
def save_legit(data):
    with open(LEGIT_FILE, "w") as f:
        json.dump(data, f, indent=4)

@bot.tree.command(name="legit", description="Xem số legit của cửa hàng.")
async def legit(interaction: discord.Interaction):
    legit_data = load_legit()
    store_legit = legit_data.get("store", 0)
    
    embed = discord.Embed(
        title="✅ Legit Store ✅",
        description=f"Số legit hiện tại của cửa hàng: `{store_legit}`",
        color=discord.Color.blue()
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="add_legit", description="Thêm legit cho người dùng (Chỉ admin hoặc buyer)")
async def add_legit(interaction: discord.Interaction, user: discord.Member):
    if interaction.user.id != ADMIN_ID and not any(role.id == BUYER_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message("🚫 Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
        return
    
    legit_data = load_legit()
    legit_data[str(user.id)] = legit_data.get(str(user.id), 0) + 1
    legit_data["store"] = legit_data.get("store", 0) + 1
    save_legit(legit_data)
    
    await interaction.response.send_message(f"✅ **{user.mention} đã nhận được 1 legit từ {interaction.user.mention}!**")
@bot.event
async def on_ready():
    global stock_data
    stock_data = load_stock()  # Cập nhật stock khi bot online
    await bot.tree.sync()  # Đồng bộ Slash Command
    print(f'✅ Bot {bot.user} đã sẵn sàng!')


@bot.tree.command(name="napthe", description="Gửi yêu cầu nạp thẻ lên admin.")
async def napthe(interaction: discord.Interaction):
    await interaction.response.send_modal(NapThe())

bot.run(TOKEN)
