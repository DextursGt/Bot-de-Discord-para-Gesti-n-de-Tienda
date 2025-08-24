# Importamos las librerías necesarias para la tienda virtual
import discord
from discord.ext import commands
from discord import ui
from typing import List, Dict, Optional
import logging
# Traemos los módulos de la tienda y economía
from virtual_shop import virtual_shop
from data_manager import load_data, save_data
from economy_system import EconomySystem
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class VirtualShopView(discord.ui.View):
    """Vista principal de la tienda virtual donde los usuarios pueden navegar y comprar productos"""
    
    def __init__(self, user_id: int, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.user_id = user_id  # ID del usuario que abrió la tienda
        self.current_category = "all"  # Categoría actual seleccionada
        self.current_page = 0  # Página actual de productos
        self.products_per_page = 5  # Cantidad de productos por página
    
    async def on_timeout(self):
        """Deshabilita todos los botones cuando la vista expira por tiempo"""
        for item in self.children:
            item.disabled = True  # Deshabilitamos todos los controles
        
        try:
            await self.message.edit(view=self)  # Intentamos actualizar la vista
        except:
            pass  # Ignoramos errores si el mensaje ya no existe
    
    def get_filtered_products(self):
        """Filtra los productos según la categoría seleccionada"""
        all_products = virtual_shop.get_virtual_products()
        
        # Filtramos solo productos habilitados
        enabled_products = {k: v for k, v in all_products.items() if v.get('enabled', True)}
        
        if self.current_category == "all":
            return enabled_products  # Devolvemos todos los productos
        
        # Filtramos por categoría específica
        return {k: v for k, v in enabled_products.items() if v.get('category') == self.current_category}
    
    def create_shop_embed(self):
        """Crea el embed principal que muestra los productos de la tienda"""
        economy = EconomySystem()
        user_coins = economy.get_balance(str(self.user_id))  # Obtenemos el balance del usuario
        
        filtered_products = self.get_filtered_products()  # Productos filtrados por categoría
        total_products = len(filtered_products)
        
        # Calculamos la paginación de productos
        start_idx = self.current_page * self.products_per_page
        end_idx = start_idx + self.products_per_page
        products_list = list(filtered_products.items())[start_idx:end_idx]
        
        # Creamos el embed principal de la tienda
        embed = discord.Embed(
            title="🛒 Tienda Virtual de GameCoins",
            description=f"💰 Tus GameCoins: **{user_coins:,}**",
            color=0x3498db  # Color azul para la tienda
        )
        
        # Información de la categoría actual
        if self.current_category == "all":
            category_name = "📦 Todas las Categorías"
        else:
            category_info = virtual_shop.categories.get(self.current_category, {"name": "Sin Categoría", "emoji": "📦"})
            category_name = f"{category_info['emoji']} {category_info['name']}"
        
        embed.add_field(
            name="📂 Categoría Actual",
            value=category_name,
            inline=True
        )
        
        # Calculamos el número total de páginas
        total_pages = (total_products + self.products_per_page - 1) // self.products_per_page
        if total_pages == 0:
            total_pages = 1  # Mínimo una página
        
        embed.add_field(
            name="📄 Página",
            value=f"{self.current_page + 1}/{total_pages}",
            inline=True
        )
        
        embed.add_field(
            name="📦 Productos",
            value=f"{total_products} disponibles",
            inline=True
        )
        
        # Mostramos los productos en el embed
        if not products_list:
            embed.add_field(
                name="🚫 Sin Productos",
                value="No hay productos disponibles en esta categoría.",
                inline=False
            )
        else:
            for i, (product_id, product) in enumerate(products_list, 1):
                # Verificamos si el usuario puede permitirse el producto
                can_afford = user_coins >= product['price']
                price_display = f"💰 **{product['price']:,}** GameCoins"
                if not can_afford:
                    price_display += " ❌"  # Indicamos que no puede comprarlo
                
                # Agregamos información adicional del producto
                extra_info = []
                if product.get('role_id'):
                    extra_info.append("🎭 Incluye rol")
                if product.get('duration_days'):
                    extra_info.append(f"⏰ {product['duration_days']} días")
                
                value = f"{price_display}\n📝 {product['description']}"
                if extra_info:
                    value += f"\n{' • '.join(extra_info)}"
                value += f"\n🆔 `{product_id}`"  # ID del producto
                
                embed.add_field(
                    name=f"{start_idx + i}. {product['name']}",
                    value=value,
                    inline=False
                )
        
        embed.set_footer(text="Usa los botones para navegar y comprar productos")
        return embed
    
    def update_buttons(self):
        """Actualiza el estado de habilitación de los botones según el contexto"""
        filtered_products = self.get_filtered_products()
        total_products = len(filtered_products)
        total_pages = max(1, (total_products + self.products_per_page - 1) // self.products_per_page)
        
        # Controlamos la navegación entre páginas
        self.previous_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page >= total_pages - 1
        
        # El botón de compra solo está disponible si hay productos
        self.buy_product.disabled = total_products == 0
    
    @discord.ui.select(
        placeholder="🔍 Selecciona una categoría...",
        options=[
            discord.SelectOption(label="📦 Todas las Categorías", value="all", emoji="📦"),
            discord.SelectOption(label="🎭 Roles", value="roles", emoji="🎭"),
            discord.SelectOption(label="⭐ Beneficios", value="perks", emoji="⭐"),
            discord.SelectOption(label="🎁 Items", value="items", emoji="🎁"),
            discord.SelectOption(label="✨ Cosméticos", value="cosmetics", emoji="✨"),
            discord.SelectOption(label="📦 Otros", value="other", emoji="📦")
        ]
    )
    async def category_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Maneja el cambio de categoría seleccionada por el usuario"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Solo quien abrió la tienda puede usarla.", ephemeral=True)
            return
        
        self.current_category = select.values[0]
        self.current_page = 0  # Reinicia a la primera página
        
        self.update_buttons()
        embed = self.create_shop_embed()
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="⬅️ Anterior", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Navega a la página anterior de productos"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Solo quien abrió la tienda puede usarla.", ephemeral=True)
            return
        
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            embed = self.create_shop_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="➡️ Siguiente", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Navega a la página siguiente de productos"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Solo quien abrió la tienda puede usarla.", ephemeral=True)
            return
        
        filtered_products = self.get_filtered_products()
        total_pages = max(1, (len(filtered_products) + self.products_per_page - 1) // self.products_per_page)
        
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_buttons()
            embed = self.create_shop_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="🛍️ Comprar", style=discord.ButtonStyle.success)
    async def buy_product(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Abre el modal de compra para que el usuario seleccione un producto"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Solo quien abrió la tienda puede usarla.", ephemeral=True)
            return
        
        filtered_products = self.get_filtered_products()
        if not filtered_products:
            await interaction.response.send_message("❌ No hay productos disponibles para comprar.", ephemeral=True)
            return
        
        modal = PurchaseModal(self.user_id, filtered_products)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🔄 Actualizar", style=discord.ButtonStyle.primary)
    async def refresh_shop(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Actualiza la vista de la tienda con los datos más recientes"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Solo quien abrió la tienda puede usarla.", ephemeral=True)
            return
        
        self.update_buttons()
        embed = self.create_shop_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="❌ Cerrar", style=discord.ButtonStyle.danger)
    async def close_shop(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cierra la interfaz de la tienda virtual"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Solo quien abrió la tienda puede usarla.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🛒 Tienda Virtual Cerrada",
            description="¡Gracias por visitar la tienda virtual!",
            color=0x95a5a6
        )
        
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)

class PurchaseModal(discord.ui.Modal):
    """Modal para que el usuario ingrese el ID del producto a comprar"""
    
    def __init__(self, user_id: int, available_products: dict):
        super().__init__(title="🛍️ Comprar Producto")
        self.user_id = user_id
        self.available_products = available_products
        
        self.product_id = discord.ui.TextInput(
            label="ID del Producto",
            placeholder="Ingresa el ID del producto que deseas comprar...",
            required=True,
            max_length=50
        )
        self.add_item(self.product_id)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Procesa la compra del producto seleccionado"""
        try:
            await interaction.response.defer()
            
            product_id = self.product_id.value.strip()
            
            # Verifica que el producto existe y está disponible
            if product_id not in self.available_products:
                await interaction.followup.send("❌ Producto no encontrado o no disponible.", ephemeral=True)
                return
            
            product = self.available_products[product_id]
            
            # Verifica el balance de GameCoins del usuario
            economy = EconomySystem()
            user_coins = economy.get_balance(str(self.user_id))
            
            if user_coins < product['price']:
                needed = product['price'] - user_coins
                await interaction.followup.send(
                    f"❌ No tienes suficientes GameCoins.\n"
                    f"💰 Tienes: {user_coins:,}\n"
                    f"💰 Necesitas: {product['price']:,}\n"
                    f"💰 Te faltan: {needed:,}",
                    ephemeral=True
                )
                return
            
            # Procesa la compra del producto
            purchase_result = virtual_shop.purchase_virtual_product(
                user_id=str(self.user_id),
                product_id=product_id,
                guild_id=str(interaction.guild.id) if interaction.guild else None
            )
            
            if purchase_result['success']:
                # Deduce las monedas del balance del usuario
                economy.remove_coins(str(self.user_id), product['price'], f"Compra: {product['name']}")
                new_balance = economy.get_balance(str(self.user_id))
                
                # Otorga el rol si el producto lo incluye
                role_granted = False
                if product.get('role_id') and interaction.guild:
                    try:
                        role = interaction.guild.get_role(int(product['role_id']))
                        if role and role not in interaction.user.roles:
                            await interaction.user.add_roles(role)
                            role_granted = True
                    except Exception as e:
                        logger.error(f"Error al otorgar rol: {e}")
                
                # Crea el embed de confirmación de compra
                embed = discord.Embed(
                    title="✅ Compra Exitosa",
                    description=f"¡Has comprado **{product['name']}** exitosamente!",
                    color=0x00ff00
                )
                
                embed.add_field(name="💰 Precio", value=f"{product['price']:,} GameCoins", inline=True)
                embed.add_field(name="💰 Saldo Restante", value=f"{new_balance:,} GameCoins", inline=True)
                
                if role_granted:
                    embed.add_field(name="🎭 Rol Otorgado", value=f"<@&{product['role_id']}>", inline=False)
                
                if product.get('duration_days'):
                    expiry_date = datetime.now() + timedelta(days=product['duration_days'])
                    embed.add_field(
                        name="⏰ Válido hasta",
                        value=f"<t:{int(expiry_date.timestamp())}:F>",
                        inline=False
                    )
                
                embed.add_field(name="📝 Descripción", value=product['description'], inline=False)
                embed.set_footer(text=f"Compra ID: {purchase_result['purchase_id']}")
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                # Registra la compra en los logs
                logger.info(f"Usuario {self.user_id} compró {product['name']} por {product['price']} GameCoins")
                
            else:
                await interaction.followup.send(
                    f"❌ Error al procesar la compra: {purchase_result.get('error', 'Error desconocido')}",
                    ephemeral=True
                )
        
        except Exception as e:
            logger.error(f"Error en compra de producto virtual: {e}")
            await interaction.followup.send("❌ Error al procesar la compra. Intenta de nuevo.", ephemeral=True)

class MyPurchasesView(discord.ui.View):
    """Vista para mostrar las compras del usuario"""
    
    def __init__(self, user_id: int, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.current_page = 0
        self.purchases_per_page = 5
    
    async def on_timeout(self):
        """Deshabilita los botones cuando expira el tiempo"""
        for item in self.children:
            item.disabled = True
        
        try:
            await self.message.edit(view=self)
        except:
            pass
    
    def get_user_purchases(self):
        """Obtiene las compras del usuario"""
        return virtual_shop.get_user_purchases(str(self.user_id))
    
    def create_purchases_embed(self):
        """Crea el embed de compras del usuario"""
        purchases = self.get_user_purchases()
        total_purchases = len(purchases)
        
        # Calcular paginación
        start_idx = self.current_page * self.purchases_per_page
        end_idx = start_idx + self.purchases_per_page
        purchases_list = purchases[start_idx:end_idx]
        
        embed = discord.Embed(
            title="🛍️ Mis Compras",
            description=f"Total de compras: {total_purchases}",
            color=0x9b59b6
        )
        
        # Información de paginación
        total_pages = max(1, (total_purchases + self.purchases_per_page - 1) // self.purchases_per_page)
        embed.add_field(
            name="📄 Página",
            value=f"{self.current_page + 1}/{total_pages}",
            inline=True
        )
        
        # Calcular total gastado
        total_spent = sum(purchase.get('price_paid', 0) for purchase in purchases)
        embed.add_field(
            name="💰 Total Gastado",
            value=f"{total_spent:,} GameCoins",
            inline=True
        )
        
        # Mostrar compras
        if not purchases_list:
            embed.add_field(
                name="🚫 Sin Compras",
                value="No has realizado compras aún.",
                inline=False
            )
        else:
            for i, purchase in enumerate(purchases_list, 1):
                status = "✅ Activo" if purchase.get('active', True) else "❌ Inactivo"
                
                # Formatear fecha
                purchase_date = datetime.fromisoformat(purchase['purchase_date'])
                date_str = f"<t:{int(purchase_date.timestamp())}:d>"
                
                value = f"💰 {purchase.get('price_paid', 0):,} GameCoins\n"
                value += f"📅 {date_str}\n"
                value += f"🔄 {status}"
                
                embed.add_field(
                    name=f"{start_idx + i}. {purchase['product_name']}",
                    value=value,
                    inline=True
                )
        
        embed.set_footer(text="Historial de compras en la tienda virtual")
        return embed
    
    def update_buttons(self):
        """Actualiza el estado de los botones"""
        purchases = self.get_user_purchases()
        total_purchases = len(purchases)
        total_pages = max(1, (total_purchases + self.purchases_per_page - 1) // self.purchases_per_page)
        
        self.previous_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page >= total_pages - 1
    
    @discord.ui.button(label="⬅️ Anterior", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Página anterior"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Solo quien solicitó la información puede usarla.", ephemeral=True)
            return
        
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            embed = self.create_purchases_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="➡️ Siguiente", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Página siguiente"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Solo quien solicitó la información puede usarla.", ephemeral=True)
            return
        
        purchases = self.get_user_purchases()
        total_pages = max(1, (len(purchases) + self.purchases_per_page - 1) // self.purchases_per_page)
        
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_buttons()
            embed = self.create_purchases_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="🔄 Actualizar", style=discord.ButtonStyle.primary)
    async def refresh_purchases(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Actualiza la lista de compras"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Solo quien solicitó la información puede usarla.", ephemeral=True)
            return
        
        self.update_buttons()
        embed = self.create_purchases_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="❌ Cerrar", style=discord.ButtonStyle.danger)
    async def close_purchases(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cierra la vista de compras"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Solo quien solicitó la información puede usarla.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🛍️ Compras Cerradas",
            description="Vista de compras cerrada.",
            color=0x95a5a6
        )
        
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)