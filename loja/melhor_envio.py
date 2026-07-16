from decimal import Decimal

import requests
from django.conf import settings


class MelhorEnvioError(Exception):
    pass


class MelhorEnvioClient:
    def __init__(self):
        self.base_url = settings.MELHOR_ENVIO_BASE_URL.rstrip('/')
        self.token = settings.MELHOR_ENVIO_TOKEN
        self.user_agent = settings.MELHOR_ENVIO_USER_AGENT

    def configurado(self):
        return bool(self.token)

    def _headers(self):
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}',
            'User-Agent': self.user_agent,
        }

    def _request(self, method, path, payload=None):
        if not self.configurado():
            raise MelhorEnvioError('Configure MELHOR_ENVIO_TOKEN no Render antes de usar a API.')

        url = f'{self.base_url}{path}'

        try:
            response = requests.request(
                method,
                url,
                headers=self._headers(),
                json=payload,
                timeout=25,
            )
        except requests.RequestException as exc:
            raise MelhorEnvioError(f'Falha ao conectar ao Melhor Envio: {exc}') from exc

        try:
            data = response.json()
        except ValueError:
            data = {'raw': response.text}

        if response.status_code >= 400:
            detalhe = data.get('message') if isinstance(data, dict) else None
            raise MelhorEnvioError(detalhe or f'Erro {response.status_code} no Melhor Envio: {data}')

        return data

    def criar_envio_no_carrinho(self, pedido):
        return self._request('POST', '/api/v2/me/cart', self._payload_carrinho(pedido))

    def gerar_etiqueta(self, melhor_envio_id):
        return self._request('POST', '/api/v2/me/shipment/generate', {
            'orders': [melhor_envio_id],
        })

    def imprimir_etiqueta(self, melhor_envio_id):
        return self._request('POST', '/api/v2/me/shipment/print', {
            'orders': [melhor_envio_id],
        })

    def consultar_envio(self, melhor_envio_id):
        return self._request('GET', f'/api/v2/me/orders/{melhor_envio_id}')

    def _payload_carrinho(self, pedido):
        produtos = []

        for item in pedido.itens.all():
            detalhes = []

            if item.tamanho:
                detalhes.append(f'Tam. {item.tamanho}')

            if item.cor:
                detalhes.append(item.cor)

            if item.modelagem:
                detalhes.append(item.modelagem)

            nome = item.produto.nome

            if detalhes:
                nome = f"{nome} ({' / '.join(detalhes)})"

            produtos.append({
                'name': nome,
                'quantity': item.quantidade,
                'unitary_value': str(item.produto.preco),
            })

        if not produtos:
            produtos.append({
                'name': f'Pedido VestPolo #{pedido.id}',
                'quantity': 1,
                'unitary_value': str(pedido.subtotal or pedido.total or Decimal('0')),
            })

        return {
            'service': settings.MELHOR_ENVIO_SERVICE_ID,
            'from': self._remetente(),
            'to': self._destinatario(pedido),
            'products': produtos,
            'volumes': [self._volume()],
            'options': {
                'insurance_value': str(pedido.subtotal or pedido.total or Decimal('0')),
                'receipt': False,
                'own_hand': False,
                'collect': False,
                'reverse': False,
                'non_commercial': True,
            },
        }

    def _remetente(self):
        documento = somente_digitos(settings.MELHOR_ENVIO_REMETENTE_DOCUMENTO)

        dados = {
            'name': settings.MELHOR_ENVIO_REMETENTE_NOME,
            'phone': somente_digitos(settings.MELHOR_ENVIO_REMETENTE_TELEFONE),
            'email': settings.MELHOR_ENVIO_REMETENTE_EMAIL,
            'address': settings.MELHOR_ENVIO_REMETENTE_ENDERECO,
            'number': settings.MELHOR_ENVIO_REMETENTE_NUMERO,
            'complement': settings.MELHOR_ENVIO_REMETENTE_COMPLEMENTO,
            'district': settings.MELHOR_ENVIO_REMETENTE_BAIRRO,
            'city': settings.MELHOR_ENVIO_REMETENTE_CIDADE,
            'state_abbr': settings.MELHOR_ENVIO_REMETENTE_ESTADO,
            'country_id': 'BR',
            'postal_code': somente_digitos(settings.MELHOR_ENVIO_CEP_ORIGEM),
        }

        if documento:
            dados['document'] = documento

        return dados

    def _destinatario(self, pedido):
        return {
            'name': pedido.nome_cliente or 'Cliente VestPolo',
            'phone': somente_digitos(pedido.telefone),
            'email': settings.MELHOR_ENVIO_REMETENTE_EMAIL,
            'address': pedido.endereco,
            'number': pedido.numero or 's/n',
            'complement': pedido.complemento,
            'district': pedido.bairro,
            'city': pedido.cidade,
            'state_abbr': pedido.estado,
            'country_id': 'BR',
            'postal_code': somente_digitos(pedido.cep_entrega),
        }

    def _volume(self):
        return {
            'height': settings.MELHOR_ENVIO_ALTURA,
            'width': settings.MELHOR_ENVIO_LARGURA,
            'length': settings.MELHOR_ENVIO_COMPRIMENTO,
            'weight': str(settings.MELHOR_ENVIO_PESO),
        }


def somente_digitos(valor):
    return ''.join(filter(str.isdigit, str(valor or '')))


def primeiro_valor(data, chaves):
    if isinstance(data, dict):
        for chave in chaves:
            valor = data.get(chave)
            if valor:
                return str(valor)

        for valor in data.values():
            encontrado = primeiro_valor(valor, chaves)
            if encontrado:
                return encontrado

    if isinstance(data, list):
        for item in data:
            encontrado = primeiro_valor(item, chaves)
            if encontrado:
                return encontrado

    return ''
