from __future__ import annotations

from dataclasses import dataclass
import mimetypes
from pathlib import Path
from typing import Any

from .commands import IntegrationConfigError


WECHAT_TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
WECHAT_UPLOAD_ARTICLE_IMAGE_URL = "https://api.weixin.qq.com/cgi-bin/media/uploadimg"
WECHAT_ADD_MATERIAL_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material"
WECHAT_DRAFT_ADD_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"


@dataclass(frozen=True)
class WechatArticleDraftInput:
    title: str
    author: str
    digest: str
    content: str
    content_source_url: str
    thumb_media_id: str


def select_cover_image(explicit_cover: str | None, document_images: list[str]) -> str | None:
    if explicit_cover:
        return explicit_cover
    if document_images:
        return document_images[0]
    return None


class WechatPublisher:
    def __init__(self, *, app_id: str, app_secret: str) -> None:
        self._app_id = app_id
        self._app_secret = app_secret
        self._access_token: str | None = None

    def build_draft_payload(self, draft: WechatArticleDraftInput) -> dict[str, Any]:
        return {
            "articles": [
                {
                    "title": draft.title,
                    "author": draft.author,
                    "digest": draft.digest,
                    "content": draft.content,
                    "content_source_url": draft.content_source_url,
                    "thumb_media_id": draft.thumb_media_id,
                    "need_open_comment": 0,
                    "only_fans_can_comment": 0,
                }
            ]
        }

    def get_access_token(self) -> str:
        import requests

        if self._access_token:
            return self._access_token
        response = requests.get(
            WECHAT_TOKEN_URL,
            params={
                "grant_type": "client_credential",
                "appid": self._app_id,
                "secret": self._app_secret,
            },
            timeout=30,
        )
        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise RuntimeError(f"failed to get wechat access_token: {payload}")
        self._access_token = str(token)
        return self._access_token

    def upload_article_image(self, image_ref: str) -> str:
        payload = self._upload_file(
            endpoint=WECHAT_UPLOAD_ARTICLE_IMAGE_URL,
            image_ref=image_ref,
            params={"access_token": self.get_access_token()},
        )
        url = payload.get("url")
        if not url:
            raise RuntimeError(f"failed to upload wechat article image: {payload}")
        return str(url)

    def upload_cover_image(self, image_ref: str) -> str:
        payload = self._upload_file(
            endpoint=WECHAT_ADD_MATERIAL_URL,
            image_ref=image_ref,
            params={"access_token": self.get_access_token(), "type": "image"},
        )
        media_id = payload.get("media_id")
        if not media_id:
            raise RuntimeError(f"failed to upload wechat cover image: {payload}")
        return str(media_id)

    def create_draft(self, draft: WechatArticleDraftInput) -> dict[str, Any]:
        import requests
        import json

        response = requests.post(
            WECHAT_DRAFT_ADD_URL,
            params={"access_token": self.get_access_token()},
            data=json.dumps(self.build_draft_payload(draft), ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=30,
        )
        payload = response.json()
        if payload.get("errcode") not in (None, 0):
            raise RuntimeError(f"failed to create wechat draft: {payload}")
        return payload

    def _upload_file(self, *, endpoint: str, image_ref: str, params: dict[str, Any]) -> dict[str, Any]:
        import requests

        if image_ref.startswith("http://") or image_ref.startswith("https://"):
            response = requests.get(image_ref, timeout=60)
            response.raise_for_status()
            content = response.content
            filename = image_ref.rstrip("/").split("/")[-1] or "image.png"
        else:
            path = Path(image_ref).expanduser()
            content = path.read_bytes()
            filename = path.name

        mime_type = mimetypes.guess_type(filename)[0] or "image/png"
        response = requests.post(
            endpoint,
            params=params,
            files={"media": (filename, content, mime_type)},
            timeout=60,
        )
        payload = response.json()
        if payload.get("errcode") not in (None, 0):
            raise RuntimeError(f"wechat upload failed: {payload}")
        return payload


def require_cover_image(explicit_cover: str | None, document_images: list[str]) -> str:
    cover = select_cover_image(explicit_cover, document_images)
    if not cover:
        raise IntegrationConfigError("wechat draft requires a cover image; provide --cover-image or include at least one image in the Feishu doc")
    return cover
