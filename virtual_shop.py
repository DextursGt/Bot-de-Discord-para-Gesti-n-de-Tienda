# Importamos todo lo que necesitamos para que funcione nuestra tienda virtual
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from data_manager import load_data, save_data
from economy_system import economy

class VirtualShop:
    """Esta es nuestra tienda virtual donde los usuarios pueden comprar cosas geniales"""
    
    def __init__(self):
        """Aquí definimos todas las categorías disponibles en nuestra tienda"""
        self.categories = {
            "roles": {"name": "Roles", "emoji": "🎭"},      # Roles especiales para el servidor
            "perks": {"name": "Beneficios", "emoji": "⭐"},  # Ventajas y beneficios únicos
            "items": {"name": "Items", "emoji": "🎁"},      # Objetos y artículos virtuales
            "cosmetics": {"name": "Cosméticos", "emoji": "✨"}, # Para verse más cool
            "other": {"name": "Otros", "emoji": "📦"}       # Todo lo demás que no encaja
        }
    
    def get_virtual_products(self) -> Dict:
        """Trae todos los productos que tenemos disponibles en la tienda"""
        data = load_data()
        
        # Si es la primera vez, creamos la estructura de la tienda
        if "virtual_shop" not in data:
            data["virtual_shop"] = {
                "products": {},    # Aquí guardamos todos los productos
                "purchases": {},   # Aquí las compras de los usuarios
                "settings": {"enabled": True, "tax_rate": 0.0}  # Configuración general
            }
            save_data(data)
        
        products = data["virtual_shop"]["products"]
        
        # A veces los datos pueden estar en formato incorrecto, los arreglamos
        if isinstance(products, list):
            # Si está como lista, lo convertimos a diccionario
            products_dict = {str(i): product for i, product in enumerate(products)}
            data["virtual_shop"]["products"] = products_dict
            save_data(data)
            return products_dict
        elif not isinstance(products, dict):
            # Si no es ni lista ni diccionario, empezamos de cero
            data["virtual_shop"]["products"] = {}
            save_data(data)
            return {}
        
        return products
    
    def add_virtual_product(self, name: str, price: int, description: str, 
                           category: str = "other", image_url: str = None,
                           role_id: str = None, duration_days: int = None) -> str:
        """Agrega un nuevo producto genial a nuestra tienda virtual"""
        data = load_data()
        
        # Si no existe la tienda, la creamos desde cero
        if "virtual_shop" not in data:
            data["virtual_shop"] = {"products": {}, "purchases": {}, "settings": {"enabled": True, "tax_rate": 0.0}}
        
        # Generamos un ID único para el producto (como una huella digital)
        product_id = str(uuid.uuid4())
        
        # Creamos toda la información del producto
        product_data = {
            "id": product_id,              # Su identificador único
            "name": name,                  # Nombre que verán los usuarios
            "price": price,                # Cuánto cuesta en GameCoins
            "description": description,    # Descripción atractiva
            "category": category,          # En qué categoría va
            "image_url": image_url,        # Imagen para que se vea bonito
            "role_id": role_id,            # Si da un rol especial
            "duration_days": duration_days, # Si es temporal, cuántos días dura
            "created_at": datetime.utcnow().isoformat(), # Cuándo lo creamos
            "enabled": True,               # Si está disponible para comprar
            "purchases_count": 0           # Cuántas veces lo han comprado
        }
        
        # Guardamos el producto en nuestra base de datos
        data["virtual_shop"]["products"][product_id] = product_data
        save_data(data)
        
        return product_id  # Devolvemos el ID para referencia
    
    def remove_virtual_product(self, product_id: str) -> bool:
        """Elimina un producto de la tienda (¡cuidado, no se puede deshacer!)"""
        data = load_data()
        
        # Verificamos que el producto existe antes de eliminarlo
        if "virtual_shop" in data and product_id in data["virtual_shop"]["products"]:
            del data["virtual_shop"]["products"][product_id]  # ¡Adiós producto!
            save_data(data)
            return True  # Éxito, producto eliminado
        return False  # No se pudo eliminar (probablemente no existía)
    
    def edit_virtual_product(self, product_id: str, **kwargs) -> bool:
        """Modifica un producto existente (para cuando queremos cambiar algo)"""
        data = load_data()
        
        # Verificamos que el producto existe
        if "virtual_shop" in data and product_id in data["virtual_shop"]["products"]:
            product = data["virtual_shop"]["products"][product_id]
            
            # Solo permitimos cambiar ciertos campos por seguridad
            allowed_fields = ['name', 'price', 'description', 'category', 'image_url', 
                            'role_id', 'duration_days', 'enabled']
            
            # Actualizamos solo los campos que nos enviaron y que están permitidos
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None:
                    product[field] = value  # Aplicamos el cambio
            
            save_data(data)  # Guardamos los cambios
            return True  # Todo salió bien
        return False  # El producto no existe
    
    def purchase_virtual_product(self, user_id: str, product_id: str) -> Dict[str, Any]:
        """¡Aquí es donde la magia sucede! Procesamos la compra de un producto"""
        data = load_data()
        
        # Primero verificamos que el producto realmente existe
        if "virtual_shop" not in data or product_id not in data["virtual_shop"]["products"]:
            return {"success": False, "message": "¡Ups! Ese producto no existe 😅"}
        
        product = data["virtual_shop"]["products"][product_id]
        
        # Verificamos que el producto esté disponible para comprar
        if not product.get("enabled", True):
            return {"success": False, "message": "Este producto no está disponible ahora mismo 😔"}
        
        # ¡Momento de la verdad! ¿Tiene suficiente dinero?
        user_balance = economy.get_balance(user_id)
        if user_balance < product["price"]:
            return {
                "success": False, 
                "message": f"¡Te faltan monedas! Necesitas {product['price']:,} GameCoins, pero solo tienes {user_balance:,} 💰"
            }
        
        # ¡Perfecto! Vamos a procesar la compra
        try:
            # Le quitamos las monedas de su cuenta
            economy.remove_coins(user_id, product["price"])
            
            # Creamos un registro de la compra para el historial
            purchase_id = str(uuid.uuid4())  # ID único para esta compra
            purchase_data = {
                "id": purchase_id,                              # Identificador único
                "user_id": user_id,                            # Quién lo compró
                "product_id": product_id,                      # Qué compró
                "product_name": product["name"],               # Nombre del producto
                "price_paid": product["price"],                # Cuánto pagó
                "purchased_at": datetime.utcnow().isoformat(), # Cuándo lo compró
                "active": True                                 # Si está activo
            }
            
            # Nos aseguramos de que existe la sección de compras
            if "purchases" not in data["virtual_shop"]:
                data["virtual_shop"]["purchases"] = {}
            data["virtual_shop"]["purchases"][purchase_id] = purchase_data
            
            # Aumentamos el contador de cuántas veces se ha comprado este producto
            data["virtual_shop"]["products"][product_id]["purchases_count"] += 1
            
            save_data(data)  # Guardamos todo
            
            return {
                "success": True,
                "message": f"¡Compra exitosa! Has adquirido **{product['name']}**",
                "purchase_id": purchase_id,
                "product": product
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error al procesar la compra: {str(e)}"}
    
    def get_user_purchases(self, user_id: str) -> List[Dict]:
        """Obtiene las compras de un usuario"""
        data = load_data()
        
        if "virtual_shop" not in data or "purchases" not in data["virtual_shop"]:
            return []
        
        purchases = data["virtual_shop"]["purchases"]
        
        # Verificar si purchases es una lista, convertir a diccionario
        if isinstance(purchases, list):
            purchases_dict = {str(i): purchase for i, purchase in enumerate(purchases)}
            data["virtual_shop"]["purchases"] = purchases_dict
            save_data(data)
            purchases = purchases_dict
        elif not isinstance(purchases, dict):
            return []
        
        user_purchases = []
        for purchase_id, purchase in purchases.items():
            if isinstance(purchase, dict) and purchase.get("user_id") == user_id and purchase.get("active", True):
                user_purchases.append(purchase)
        
        return sorted(user_purchases, key=lambda x: x.get("purchased_at", ""), reverse=True)
    
    def deactivate_purchase(self, purchase_id: str) -> bool:
        """Desactiva una compra (para productos temporales)"""
        data = load_data()
        
        if "virtual_shop" in data and "purchases" in data["virtual_shop"] and purchase_id in data["virtual_shop"]["purchases"]:
            data["virtual_shop"]["purchases"][purchase_id]["active"] = False
            save_data(data)
            return True
        return False
    
    def get_products_by_category(self) -> Dict[str, List[Dict]]:
        """Organiza productos por categoría"""
        products = self.get_virtual_products()
        categorized = {cat: [] for cat in self.categories.keys()}
        
        for product_id, product in products.items():
            if product.get("enabled", True):
                category = product.get("category", "other")
                if category not in categorized:
                    category = "other"
                categorized[category].append(product)
        
        return categorized
    
    def get_shop_stats(self) -> Dict:
        """Obtiene estadísticas de la tienda virtual"""
        data = load_data()
        if "virtual_shop" not in data:
            return {"total_products": 0, "total_purchases": 0, "total_revenue": 0, "enabled_products": 0}
        
        products = data["virtual_shop"].get("products", {})
        purchases = data["virtual_shop"].get("purchases", {})
        
        # Verificar si purchases es un diccionario, si no, convertirlo
        if isinstance(purchases, list):
            # Si es una lista, convertir a diccionario usando índices
            purchases = {str(i): purchase for i, purchase in enumerate(purchases)}
        elif not isinstance(purchases, dict):
            purchases = {}
        
        # Verificar si products es un diccionario
        if isinstance(products, list):
            products = {str(i): product for i, product in enumerate(products)}
        elif not isinstance(products, dict):
            products = {}
        
        total_revenue = sum(purchase["price_paid"] for purchase in purchases.values() if isinstance(purchase, dict) and purchase.get("active", True))
        active_purchases = len([p for p in purchases.values() if isinstance(p, dict) and p.get("active", True)])
        
        return {
            "total_products": len(products),
            "total_purchases": active_purchases,
            "total_revenue": total_revenue,
            "enabled_products": len([p for p in products.values() if isinstance(p, dict) and p.get("enabled", True)])
        }

# Instancia global de la tienda virtual
virtual_shop = VirtualShop()