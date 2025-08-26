import aiohttp
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from data_manager import load_data, save_data

logger = logging.getLogger(__name__)

class ExchangeRateManager:
    def __init__(self):
        # API gratuita de exchangerate-api.com usando USD como base
        self.api_url = "https://api.exchangerate-api.com/v4/latest/USD"
        self.cache_duration = timedelta(hours=1)  # Actualizar cada hora
        self.fallback_rates = {
            "ARS": 72.3,  # 1 MXN = 72.3 ARS
            "COP": 216.0  # 1 MXN = 216 COP
        }
    
    async def get_exchange_rates(self) -> Dict[str, float]:
        """Obtiene las tasas de cambio, usando caché si está disponible y actualizado"""
        try:
            # Verificar caché primero
            cached_rates = self._get_cached_rates()
            if cached_rates:
                logger.info("Usando tasas de cambio desde caché")
                return cached_rates
            
            # Obtener tasas frescas de la API
            fresh_rates = await self._fetch_fresh_rates()
            if fresh_rates:
                self._cache_rates(fresh_rates)
                logger.info("Tasas de cambio actualizadas desde API")
                return fresh_rates
            
            # Fallback a tasas predeterminadas
            logger.warning("Usando tasas de cambio predeterminadas")
            return self.fallback_rates
            
        except Exception as e:
            logger.error(f"Error obteniendo tasas de cambio: {e}")
            return self.fallback_rates
    
    def _get_cached_rates(self) -> Optional[Dict[str, float]]:
        """Obtiene tasas de cambio del caché si están actualizadas"""
        try:
            data = load_data()
            
            if "exchange_rates" not in data:
                return None
            
            cache_data = data["exchange_rates"]
            
            # Verificar si el caché ha expirado
            last_updated = datetime.fromisoformat(cache_data.get("last_updated", ""))
            if datetime.now() - last_updated > self.cache_duration:
                return None
            
            rates = cache_data.get("rates", {})
            
            # Verificar que tenemos todas las monedas necesarias (sin MXN ya que es la base)
            required_currencies = ["ARS", "COP"]
            if all(currency in rates for currency in required_currencies):
                return {currency: rates[currency] for currency in required_currencies}
            
            return None
            
        except Exception as e:
            logger.error(f"Error leyendo caché de tasas de cambio: {e}")
            return None
    
    async def _fetch_fresh_rates(self) -> Optional[Dict[str, float]]:
        """Obtiene tasas de cambio frescas de la API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        rates = data.get("rates", {})
                        
                        # Extraer solo las monedas que necesitamos (sin MXN ya que es la base)
                        required_currencies = ["ARS", "COP"]
                        filtered_rates = {}
                        
                        for currency in required_currencies:
                            if currency in rates:
                                filtered_rates[currency] = float(rates[currency])
                            else:
                                # Si falta alguna moneda, usar fallback
                                filtered_rates[currency] = self.fallback_rates[currency]
                        
                        return filtered_rates
                    
                    else:
                        logger.error(f"API respondió con código {response.status}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error("Timeout al obtener tasas de cambio de la API")
            return None
        except Exception as e:
            logger.error(f"Error obteniendo tasas de cambio de la API: {e}")
            return None
    
    def _cache_rates(self, rates: Dict[str, float]):
        """Guarda las tasas de cambio en caché"""
        try:
            data = load_data()
            
            data["exchange_rates"] = {
                "rates": rates,
                "last_updated": datetime.now().isoformat(),
                "source": "exchangerate-api.com"
            }
            
            save_data(data)
            logger.info("Tasas de cambio guardadas en caché")
            
        except Exception as e:
            logger.error(f"Error guardando tasas de cambio en caché: {e}")
    
    def get_country_info(self) -> Dict[str, Dict]:
        """Retorna información de países con sus monedas"""
        return {
            "mexico": {
                "name": "🇲🇽 México",
                "currency": "MXN",
                "currency_symbol": "$",
                "flag": "🇲🇽"
            },
            "argentina": {
                "name": "🇦🇷 Argentina", 
                "currency": "ARS",
                "currency_symbol": "$",
                "flag": "🇦🇷"
            },
            "colombia": {
                "name": "🇨🇴 Colombia",
                "currency": "COP",
                "currency_symbol": "$",
                "flag": "🇨🇴"
            }
        }
    
    async def convert_price(self, price_mxn: float, target_currency: str) -> float:
        """Convierte precio de MXN a moneda local"""
        try:
            # Si la moneda objetivo es MXN, no hay conversión
            if target_currency == "MXN":
                return price_mxn
            
            # Usar directamente las tasas fallback que son correctas (MXN a target)
            if target_currency in self.fallback_rates:
                return price_mxn * self.fallback_rates[target_currency]
            else:
                logger.warning(f"Moneda {target_currency} no soportada")
                return price_mxn
                
        except Exception as e:
            logger.error(f"Error convirtiendo precio: {e}")
            # Fallback calculation
            return price_mxn * self.fallback_rates.get(target_currency, 1.0)
    
    async def get_rate_info(self) -> Dict:
        """Obtiene información sobre las tasas de cambio actuales"""
        try:
            data = load_data()
            
            if "exchange_rates" in data:
                cache_data = data["exchange_rates"]
                last_updated = cache_data.get("last_updated", "Desconocido")
                source = cache_data.get("source", "Desconocido")
                
                # Convertir timestamp a formato legible
                try:
                    last_updated_dt = datetime.fromisoformat(last_updated)
                    last_updated_str = last_updated_dt.strftime("%d/%m/%Y %H:%M")
                except:
                    last_updated_str = "Desconocido"
                
                return {
                    "last_updated": last_updated_str,
                    "source": source,
                    "rates": cache_data.get("rates", {}),
                    "is_cached": True
                }
            
            return {
                "last_updated": "Nunca",
                "source": "Tasas predeterminadas",
                "rates": self.fallback_rates,
                "is_cached": False
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo información de tasas: {e}")
            return {
                "last_updated": "Error",
                "source": "Tasas predeterminadas",
                "rates": self.fallback_rates,
                "is_cached": False
            }

# Instancia global del manager
exchange_rate_manager = ExchangeRateManager()