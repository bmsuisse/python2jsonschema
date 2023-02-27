from dataclasses import dataclass
from typing import List, Literal
import sys

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired, Required, TypedDict
else:
    from typing import NotRequired, Required, TypedDict


class TermTranslation(TypedDict):
    TermDWH: str
    TwoLetterISOCode: str
    Translation: str


class TreeTranslation(TypedDict):
    DisplayName: NotRequired[str]
    URL: NotRequired[str]
    HelpUrl: NotRequired[str]


class TreeItemData(TypedDict):
    TreeId: str
    DisplayName: str
    Type: Literal["Workspace", "iframe", "Node", "App", "Report", "PaginatedReport", "Dashboard", "Tile", "Link"]
    NameAPIOrig: NotRequired[str]
    DownloadLink: NotRequired[str]
    URL: NotRequired[str]
    EmbedURL: NotRequired[str]
    Icon: NotRequired[str]
    HelpUrl: NotRequired[str]
    Translation: NotRequired[dict[str, TreeTranslation]]
    DefaultEntryId: NotRequired[str]
    LinkTarget: NotRequired[Literal["_blank", "_self"]]  # No value equals blank on client


class TreeItems(TypedDict):
    data: TreeItemData
    Children: NotRequired[List["TreeItems"]]
    isDefault: NotRequired[bool]
    isHidden: NotRequired[bool]
    order: NotRequired[int]


@dataclass
class TreeItemConfig:
    value: List[TreeItems]
