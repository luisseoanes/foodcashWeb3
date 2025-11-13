# infrastructure/service/celo_service.py

import os
import logging
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class CeloService:
    """
    Servicio para interactuar con la blockchain de Celo y el token cCOP.
    Maneja la verificación de transacciones y consulta de balances.
    """
    
    # Dirección del contrato cCOP en Celo Mainnet
    # Esta es la dirección oficial del token cCOP (Colombian Peso) en Celo
    CCOP_CONTRACT_ADDRESS_MAINNET = "0x00Be915B9dCf56a3CBE739D9B9c202ca692409EC"  # Mainnet
    CCOP_CONTRACT_ADDRESS_SEPOLIA = os.getenv("CCOP_CONTRACT_ADDRESS_SEPOLIA")  # Sepolia Testnet - Deploy tu contrato aquí
    
    # RPC endpoints
    CELO_MAINNET_RPC = os.getenv("CELO_MAINNET_RPC_URL", "https://forno.celo.org")
    CELO_TESTNET_RPC = os.getenv("CELO_TESTNET_RPC_URL", "https://sepolia-forno.celo-testnet.org")  # Sepolia (anteriormente Alfajores)
    
    # ABI simplificado del token ERC20 (cCOP)
    ERC20_ABI = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function"
        },
        {
            "constant": False,
            "inputs": [
                {"name": "_to", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "transfer",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "from", "type": "address"},
                {"indexed": True, "name": "to", "type": "address"},
                {"indexed": False, "name": "value", "type": "uint256"}
            ],
            "name": "Transfer",
            "type": "event"
        }
    ]
    
    def __init__(self, use_testnet: bool = False):
        """
        Inicializa el servicio de Celo.
        
        Args:
            use_testnet: Si es True, usa la red de pruebas Sepolia. Si es False, usa Mainnet.
        """
        self.use_testnet = use_testnet
        
        # Configurar Web3
        rpc_url = self.CELO_TESTNET_RPC if use_testnet else self.CELO_MAINNET_RPC
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Agregar middleware para Celo (PoA)
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Verificar conexión
        if not self.w3.is_connected():
            logger.error(f"No se pudo conectar a Celo {'Sepolia Testnet' if use_testnet else 'Mainnet'}")
            raise ConnectionError(f"No se pudo conectar a Celo en {rpc_url}")
        
        logger.info(f"Conectado a Celo {'Sepolia Testnet' if use_testnet else 'Mainnet'}")
        
        # Cargar dirección de recepción de FoodCash
        self.foodcash_address = os.getenv("FOODCASH_CELO_ADDRESS")
        if not self.foodcash_address:
            logger.warning("FOODCASH_CELO_ADDRESS no configurada en .env")
        else:
            # Convertir a checksum address
            self.foodcash_address = self.w3.to_checksum_address(self.foodcash_address)
            logger.info(f"Dirección de recepción FoodCash: {self.foodcash_address}")
        
        # Seleccionar dirección del contrato según la red
        if use_testnet:
            contract_address = self.CCOP_CONTRACT_ADDRESS_SEPOLIA
            if not contract_address:
                raise ValueError("CCOP_CONTRACT_ADDRESS_SEPOLIA no configurada en .env. Debes deployar tu contrato ERC20 en Sepolia.")
        else:
            contract_address = self.CCOP_CONTRACT_ADDRESS_MAINNET
        
        # Inicializar contrato cCOP
        self.ccop_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(contract_address),
            abi=self.ERC20_ABI
        )
        
        # Guardar dirección del contrato para referencia
        self.ccop_contract_address = contract_address
        
        # Obtener decimales del token
        try:
            self.decimals = self.ccop_contract.functions.decimals().call()
            logger.info(f"Token cCOP tiene {self.decimals} decimales")
        except Exception as e:
            logger.warning(f"No se pudo obtener decimales del token: {e}")
            self.decimals = 18  # Default para tokens ERC20
    
    def verificar_conexion(self) -> bool:
        """Verifica si la conexión a Celo está activa."""
        try:
            return self.w3.is_connected()
        except Exception as e:
            logger.error(f"Error verificando conexión: {e}")
            return False
    
    def obtener_balance_ccop(self, address: str) -> Decimal:
        """
        Obtiene el balance de cCOP de una dirección.
        
        Args:
            address: Dirección de la wallet en formato hexadecimal
            
        Returns:
            Balance en cCOP (formato decimal, no en unidades mínimas)
        """
        try:
            checksum_address = self.w3.to_checksum_address(address)
            balance_wei = self.ccop_contract.functions.balanceOf(checksum_address).call()
            balance = Decimal(balance_wei) / Decimal(10 ** self.decimals)
            logger.info(f"Balance de {address}: {balance} cCOP")
            return balance
        except Exception as e:
            logger.error(f"Error obteniendo balance de {address}: {e}")
            raise
    
    def obtener_transaccion(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los detalles de una transacción por su hash.
        
        Args:
            tx_hash: Hash de la transacción
            
        Returns:
            Diccionario con los detalles de la transacción o None si no existe
        """
        try:
            # Asegurarse de que el hash tenga el prefijo 0x
            if not tx_hash.startswith('0x'):
                tx_hash = f'0x{tx_hash}'
            
            tx = self.w3.eth.get_transaction(tx_hash)
            return {
                'hash': tx['hash'].hex(),
                'from': tx['from'],
                'to': tx['to'],
                'value': tx['value'],
                'blockNumber': tx['blockNumber'],
                'blockHash': tx['blockHash'].hex() if tx['blockHash'] else None,
                'gas': tx['gas'],
                'gasPrice': tx['gasPrice'],
                'nonce': tx['nonce'],
                'transactionIndex': tx['transactionIndex']
            }
        except Exception as e:
            logger.error(f"Error obteniendo transacción {tx_hash}: {e}")
            return None
    
    def obtener_recibo_transaccion(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el recibo de una transacción (para verificar si fue exitosa).
        
        Args:
            tx_hash: Hash de la transacción
            
        Returns:
            Diccionario con el recibo o None si no existe/está pendiente
        """
        try:
            if not tx_hash.startswith('0x'):
                tx_hash = f'0x{tx_hash}'
            
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            return {
                'transactionHash': receipt['transactionHash'].hex(),
                'blockNumber': receipt['blockNumber'],
                'status': receipt['status'],  # 1 = success, 0 = failed
                'gasUsed': receipt['gasUsed'],
                'cumulativeGasUsed': receipt['cumulativeGasUsed'],
                'logs': receipt['logs']
            }
        except Exception as e:
            logger.warning(f"Recibo no disponible para {tx_hash}: {e}")
            return None
    
    def _parsear_evento_transfer(self, log: Dict) -> Optional[Dict[str, Any]]:
        """
        Parsea un log de evento Transfer del contrato cCOP.
        
        Args:
            log: Log event del recibo de transacción
            
        Returns:
            Diccionario con from, to, y value parseados, o None si no es un Transfer
        """
        try:
            # Verificar que sea del contrato cCOP
            if log['address'].lower() != self.ccop_contract_address.lower():
                return None
            
            # El topic[0] es el hash del evento Transfer
            # Transfer(address indexed from, address indexed to, uint256 value)
            transfer_signature = self.w3.keccak(text="Transfer(address,address,uint256)").hex()
            
            if len(log['topics']) < 3 or log['topics'][0].hex() != transfer_signature:
                return None
            
            # Decodificar datos
            from_address = self.w3.to_checksum_address('0x' + log['topics'][1].hex()[-40:])
            to_address = self.w3.to_checksum_address('0x' + log['topics'][2].hex()[-40:])
            value_wei = int(log['data'], 16)
            value = Decimal(value_wei) / Decimal(10 ** self.decimals)
            
            return {
                'from': from_address,
                'to': to_address,
                'value': value,
                'value_wei': value_wei
            }
        except Exception as e:
            logger.error(f"Error parseando evento Transfer: {e}")
            return None
    
    def verificar_pago_recibido(
        self, 
        tx_hash: str, 
        monto_esperado: Decimal,
        tolerancia_porcentaje: Decimal = Decimal("0.01")  # 1% de tolerancia
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Verifica que una transacción sea un pago válido de cCOP hacia FoodCash.
        
        Args:
            tx_hash: Hash de la transacción a verificar
            monto_esperado: Monto esperado en cCOP
            tolerancia_porcentaje: Porcentaje de tolerancia en el monto (default 1%)
            
        Returns:
            Tuple (es_valido, mensaje_error, detalles_transaccion)
        """
        try:
            if not self.foodcash_address:
                return False, "Dirección de FoodCash no configurada", None
            
            # Obtener recibo de la transacción
            receipt = self.obtener_recibo_transaccion(tx_hash)
            
            if not receipt:
                return False, "Transacción no encontrada o pendiente", None
            
            # Verificar que la transacción fue exitosa
            if receipt['status'] != 1:
                return False, "La transacción falló en la blockchain", receipt
            
            # Buscar evento Transfer en los logs
            transfer_encontrado = False
            monto_recibido = None
            from_address = None
            
            for log in receipt['logs']:
                parsed = self._parsear_evento_transfer(log)
                if parsed and parsed['to'].lower() == self.foodcash_address.lower():
                    transfer_encontrado = True
                    monto_recibido = parsed['value']
                    from_address = parsed['from']
                    break
            
            if not transfer_encontrado:
                return False, "No se encontró transferencia de cCOP a FoodCash", receipt
            
            # Verificar monto con tolerancia
            monto_minimo = monto_esperado * (Decimal("1") - tolerancia_porcentaje)
            monto_maximo = monto_esperado * (Decimal("1") + tolerancia_porcentaje)
            
            if not (monto_minimo <= monto_recibido <= monto_maximo):
                return False, f"Monto incorrecto. Esperado: {monto_esperado} cCOP, Recibido: {monto_recibido} cCOP", receipt
            
            # Todo correcto
            detalles = {
                **receipt,
                'from_address': from_address,
                'to_address': self.foodcash_address,
                'amount_ccop': float(monto_recibido),
                'expected_amount': float(monto_esperado),
                'token': 'cCOP',
                'network': 'Celo Sepolia Testnet' if self.use_testnet else 'Celo Mainnet'
            }
            
            logger.info(f"Pago verificado exitosamente: {tx_hash} - {monto_recibido} cCOP")
            return True, None, detalles
            
        except Exception as e:
            logger.error(f"Error verificando pago {tx_hash}: {e}", exc_info=True)
            return False, f"Error interno: {str(e)}", None
    
    def obtener_precio_cop_ccop(self) -> Decimal:
        """
        El cCOP está anclado 1:1 con el peso colombiano.
        
        Returns:
            Siempre retorna 1.0 ya que 1 cCOP = 1 COP
        """
        return Decimal("1.0")
    
    def convertir_cop_a_ccop(self, monto_cop: Decimal) -> Decimal:
        """
        Convierte COP a cCOP.
        
        Args:
            monto_cop: Monto en pesos colombianos
            
        Returns:
            Monto equivalente en cCOP
        """
        # Como cCOP está anclado 1:1 con COP, la conversión es directa
        return monto_cop
    
    def convertir_ccop_a_cop(self, monto_ccop: Decimal) -> Decimal:
        """
        Convierte cCOP a COP.
        
        Args:
            monto_ccop: Monto en cCOP
            
        Returns:
            Monto equivalente en pesos colombianos
        """
        # Como cCOP está anclado 1:1 con COP, la conversión es directa
        return monto_ccop
    
    def obtener_info_red(self) -> Dict[str, Any]:
        """
        Obtiene información sobre la red de Celo conectada.
        
        Returns:
            Diccionario con información de la red
        """
        try:
            return {
                'connected': self.w3.is_connected(),
                'network': 'Sepolia Testnet' if self.use_testnet else 'Mainnet',
                'latest_block': self.w3.eth.block_number,
                'chain_id': self.w3.eth.chain_id,
                'gas_price': self.w3.eth.gas_price,
                'ccop_contract': self.ccop_contract_address,
                'foodcash_address': self.foodcash_address
            }
        except Exception as e:
            logger.error(f"Error obteniendo info de red: {e}")
            return {'connected': False, 'error': str(e)}