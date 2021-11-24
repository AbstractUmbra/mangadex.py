"""
The MIT License (MIT)

Copyright (c) 2021-Present AbstractUmbra

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional

from .utils import require_authentication


if TYPE_CHECKING:
    from .manga import Manga
    from .http import HTTPClient
    from .types.artist import ArtistResponse
    from .types.common import LocalisedString
    from .types.manga import MangaResponse
    from .types.relationship import RelationshipResponse


__all__ = ("Artist",)


class Artist:
    """A class representing an Artist returns from the MangaDex API.

    Attributes
    -----------
    id: :class:`str`
        The UUID associated with this artist.
    name: :class:`str`
        The artist's name.
    image_url: Optional[:class:`str`]
        The artist's image url, if any.
    biography: Optional[:class:`str`]
        The artist's biography, if any.
    twitter: Optional[:class:`str`]
        The artist's Twitter url, if any.
    pixiv: Optional[:class:`str`]
        The artist's Pixiv url, if any.
    melon_book: Optional[:class:`str`]
        The artist's Melon Book url, if any.
    booth: Optional[:class:`str`]
        The artist's Booth url, if any.
    nico_video: Optional[:class:`str`]
        The artist's Nico Video url, if any.
    skeb: Optional[:class:`str`]
        The artist's Skeb url, if any.
    fantia: Optional[:class:`str`]
        The artist's Fantia url, if any.
    tumblr: Optional[:class:`str`]
        The artist's Tumblr url, if any.
    youtube: Optional[:class:`str`]
        The artist's Youtube url, if any.
    website: Optional[:class:`str`]
        The artist's website url, if any.
    version: :class:`int`
        The version revision of this artist.
    """

    __slots__ = (
        "_http",
        "_data",
        "_attributes",
        "_relationships",
        "id",
        "name",
        "image_url",
        "biography",
        "twitter",
        "pixiv",
        "melon_book",
        "booth",
        "nico_video",
        "skeb",
        "fantia",
        "tumblr",
        "youtube",
        "website",
        "_created_at",
        "_updated_at",
        "version",
        "__manga",
    )

    def __init__(self, http: HTTPClient, payload: ArtistResponse) -> None:
        self._http = http
        self._data = payload
        self._attributes = self._data["attributes"]
        self._relationships: list[RelationshipResponse] = self._data["relationships"]
        self.id: str = self._data["id"]
        self.name: str = self._attributes["name"]
        self.image_url: Optional[str] = self._attributes["imageUrl"]
        self.biography: Optional[LocalisedString] = self._attributes["biography"]
        self.twitter: Optional[str] = self._attributes["twitter"]
        self.pixiv: Optional[str] = self._attributes["pixiv"]
        self.melon_book: Optional[str] = self._attributes["melonBook"]
        self.booth: Optional[str] = self._attributes["booth"]
        self.nico_video: Optional[str] = self._attributes["nicoVideo"]
        self.skeb: Optional[str] = self._attributes["skeb"]
        self.fantia: Optional[str] = self._attributes["fantia"]
        self.tumblr: Optional[str] = self._attributes["tumblr"]
        self.youtube: Optional[str] = self._attributes["youtube"]
        self.website: Optional[str] = self._attributes["website"]
        self.version: int = self._attributes["version"]
        self._created_at = self._attributes["createdAt"]
        self._updated_at = self._attributes["updatedAt"]
        self.__manga: Optional[list[Manga]] = None

    def __repr__(self) -> str:
        return f"<Artist id={self.id} name='{self.name}'>"

    def __str__(self) -> str:
        return self.name

    @property
    def created_at(self) -> datetime.datetime:
        """When this artist was created."""
        return datetime.datetime.fromisoformat(self._created_at)

    @property
    def updated_at(self) -> datetime.datetime:
        """When this artist was last updated."""
        return datetime.datetime.fromisoformat(self._updated_at)

    @property
    def manga(self) -> Optional[list[Manga]]:
        if self.__manga is not None:
            return self.__manga

        if not self._relationships:
            return None

        manga_: list[MangaResponse] = []
        for item in self._relationships:
            if item["type"] == "manga":
                manga_.append(item)

        if not manga_:
            return None

        formatted: list[Manga] = []
        from .manga import Manga

        for item in manga_:
            if "attributes" in item:
                formatted.append(Manga(self._http, item))

        if not formatted:
            return

        self.__manga = formatted
        return self.__manga

    @manga.setter
    def manga(self, value: list[Manga]) -> None:
        fmt = []
        for item in value:
            if isinstance(item, Manga):
                fmt.append(item)

        self.__manga = fmt

    async def get_manga(self) -> Optional[list[Manga]]:
        if self.manga is not None:
            return self.manga

        if not self._relationships:
            return

        manga_relationships: list[MangaResponse] = []
        for item in self._relationships:
            if item["type"] == "manga":
                manga_relationships.append(item)

        if not manga_relationships:
            return

        formatted: list[Manga] = []
        from .manga import Manga  # TODO: Fix circular.

        for manga in manga_relationships:
            if "attributes" in manga:
                formatted.append(Manga(self._http, manga))
            else:
                data = await self._http._view_manga(manga["id"], includes=["author", "artist", "cover_art", "manga"])
                formatted.append(Manga(self._http, data["data"]))

        if not formatted:
            return

        self.__manga = formatted
        return self.__manga

    @require_authentication
    async def update(self, *, name: Optional[str] = None, version: int) -> Artist:
        """|coro|

        This method will update the current author on the MangaDex API.

        Parameters
        -----------
        name: Optional[:class:`str`]
            The new name to update the author with.
        version: :class:`int`
            The version revision of this author.

        Raises
        -------
        :exc:`BadRequest`
            The request body was malformed.
        :exc:`Forbidden`
            You are not authorized to update this author.
        :exc:`NotFound`
            The author UUID given was not found.

        Returns
        --------
        :class:`~hondana.Artist`
            The updated author from the API.
        """
        data = await self._http._update_artist(self.id, name=name, version=version)
        return self.__class__(self._http, data["data"])

    @require_authentication
    async def delete(self) -> None:
        """|coro|

        This method will delete the current author from the MangaDex API.

        Raises
        -------
        :exc:`Forbidden`
            You are not authorized to delete this author.
        :exc:`NotFound`
            The UUID given for the author was not found.
        """
        await self._http._delete_author(self.id)
