import logging
from collections import OrderedDict
from typing import Mapping, Sequence, List
from dataclasses import dataclass, field, is_dataclass

from spoonbill.utils import get_root, combine_path, prepare_title, generate_table_name

LOGGER = logging.getLogger('spoonbill')


@dataclass
class Column:
    title: str
    type: str
    id: str
    hits: int = 0


@dataclass
class Table:
    name: str
    path: [str]
    total_rows: int = 0
    # parent is Table object but dataclasses don`t play well with recursion
    parent: object = field(default_factory=dict)
    is_root: bool = False
    is_combined: bool = False
    columns: Mapping[str, Column] = field(default_factory=OrderedDict)
    combined_columns: Mapping[str, Column] = field(default_factory=OrderedDict)
    propagated_columns: Mapping[str, Column] = field(default_factory=OrderedDict)
    additional_columns: Mapping[str, Column] = field(default_factory=OrderedDict)
    # max length not count
    arrays: Mapping[str, int] = field(default_factory=dict)
    # for headers
    titles: Mapping[str, str] = field(default_factory=dict)
    child_tables: List[str] = field(default_factory=list)
    types: Mapping[str, List[str]] = field(default_factory=dict)

    preview_rows: Sequence[dict] = field(default_factory=list, init=False)
    preview_rows_combined: Sequence[dict] = field(default_factory=list, init=False)

    def __post_init__(self):
        for attr in ('columns', 'propagated_columns',
                     'combined_columns', 'additional_columns'):
            obj = getattr(self, attr, {})
            if obj:
                init = {name: Column(**col) for name, col in obj.items() if not is_dataclass(col)}
                setattr(self, attr, init)

    def _counter(self, split, cond):
        cols = self.columns if split else self.combined_columns
        return [
            header for header, col in cols.items()
            if cond(col)
        ]

    def missing_rows(self, split=True):
        return self._counter(split, lambda c: c.hits == 0)

    def available_rows(self, split=True):
        return self._counter(split, lambda c: c.hits > 0)

    def __iter__(self):
        for col in self.columns:
            yield col

    def __getitem__(self, path):
        return self.columns.get(path)

    def add_column(self,
                   path,
                   item,
                   type_,
                   parent,
                   combined_only=False,
                   additional=False,
                   joinable=False):
        title = prepare_title(item, parent)
        column = Column(title, type_, path)
        root = get_root(self)
        combined_path = combine_path(root, path) if not joinable else path
        self.combined_columns[combined_path] = Column(title, type_, combined_path)

        for p in (path, combined_path):
            self.titles[p] = title

        if not combined_only:
            self.columns[path] = column
        if not self.is_root:
            root_table = get_root(self)
            root_table.add_column(
                path,
                item,
                type_,
                parent=parent,
                combined_only=True,
                joinable=joinable
            )
        if additional:
            self.additional_columns[path] = column

    def inc_column(self, header, combined=False):
        if combined:
            self.combined_columns[header].hits += 1
            return
        self.columns[header].hits += 1
        if header in self.additional_columns:
            self.additional_columns[header].hits += 1

    def set_array(self, header, item):
        count = self.arrays[header] or 0
        length = len(item)
        if length > count:
            self.arrays[header] = length
            return True
        return False

    def inc(self):
        self.total_rows += 1


def add_child_table(current_table, pointer, parent_key, key):
    table_name = generate_table_name(current_table.name, parent_key, key)
    child_table = Table(table_name, [pointer], parent=current_table)
    current_table.child_tables.append(table_name)
    get_root(current_table).arrays[pointer] = 0
    return child_table
