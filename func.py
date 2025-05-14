import io
import json
import base64
import datetime
import logging
import oci
import os

from fdk import response


def handler(ctx, data: io.BytesIO = None):
    try:
        # 🔹 Parse JSON vindo do FlutterFlow (POST JSON)
        body = json.loads(data.getvalue())

        usuario = body.get("usuario")
        imagem_base64 = body.get("imagem")  # Esperado em base64
        data_hora_str = body.get("data_hora")  # Ex: "2024-09-30T15:42:00"

        if not all([usuario, imagem_base64, data_hora_str]):
            return response.Response(
                ctx,
                status_code=400,
                response_data=json.dumps({"erro": "Campos obrigatórios ausentes."})
            )

        # 🔹 Converte imagem base64 para binário
        imagem_bytes = base64.b64decode(imagem_base64)

        # 🔹 Formata nome do objeto
        nome_arquivo = f"{usuario}/{data_hora_str.replace(':', '-').replace('T', '_')}.jpg"

        # 🔹 Define parâmetros OCI
        signer = oci.auth.signers.get_resource_principals_signer()
        object_storage_client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)

        namespace = object_storage_client.get_namespace().data
        bucket_name = "app-imagens-usuarios"

        # 🔹 Envia imagem para o bucket
        put_resp = object_storage_client.put_object(
            namespace_name=namespace,
            bucket_name=bucket_name,
            object_name=nome_arquivo,
            put_object_body=io.BytesIO(imagem_bytes)
        )

        return response.Response(
            ctx,
            status_code=200,
            response_data=json.dumps({
                "mensagem": "Upload realizado com sucesso!",
                "nome_objeto": nome_arquivo,
                "etag": put_resp.headers.get("etag")
            })
        )

    except Exception as e:
        logging.getLogger().error(f"Erro ao fazer upload: {str(e)}")
        return response.Response(
            ctx,
            status_code=500,
            response_data=json.dumps({"erro": str(e)})
        )
