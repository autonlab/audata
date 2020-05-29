import h5py as h5

from audata.element import AUElement


class AUGroup(AUElement):
    def __init__(self, au_parent, name=''):
        if not isinstance(au_parent, (AUElement, h5.File)):
            raise Exception(f'Invalid parent: {type(au_parent)}')

        if isinstance(au_parent, AUElement):
            parent = au_parent._h5
            if not isinstance(parent, h5.Group):
                raise Exception(f'Invalid parent: {type(parent)}')

            if name == '':
                target = parent
            else:
                if name not in parent:
                    raise Exception(f'Path {name} was not found in {parent.file.filename}:{parent.name}')
                else:
                    target = parent[name]
            if not isinstance(target, h5.Group):
                raise Exception(f'Path "{name}" is not a group in {parent.file.filename}:{parent.name}')

        super().__init__(au_parent, name)

    def list(self):
        attrs = list(self._h5.attrs)
        others = list(self._h5)
        groups = [g for g in others if isinstance(self._h5[g], h5.Group)]
        datasets = [d for d in others if isinstance(self._h5[d], h5.Dataset)]
        return {
            'attributes': attrs,
            'groups': groups,
            'datasets': datasets
        }

    def recurse(self):
        names = [n for n in list(self._h5) if not n.startswith('.')]
        for name in names:
            elem = self.__getitem__(name)
            if isinstance(elem, AUGroup):
                for stuple in elem.recurse():
                    yield stuple
            else:
                yield (elem, elem.name)

    def __repr__(self):
        lines = []
        l = self.list()
        if self.name in ('', '/'):
            lines.append('<ROOT>')
        else:
            lines.append(self.name)

        for t in l['attributes']:
            lines.append(f'  [A] {t}')
        for t in l['groups']:
            lines.append(f'  [G] {t}')
        for t in l['datasets']:
            lines.append(f'  [D] {t}')
        return '\n'.join(lines)

    def __str__(self):
        return self.__repr__()

    def __getitem__(self, key):
        if self._h5 is None:
            raise Exception('No group opened.')

        if key == '':
            return AUGroup(self, key)

        if key in self._h5:
            if isinstance(self._h5[key], h5.Dataset):
                from audata.dataset import AUDataset
                return AUDataset(self, key)
            elif isinstance(self._h5[key], h5.Group):
                return AUGroup(self, key)
            else:
                raise Exception('Unsure how to handle class: {}'.format(type(self._h5[key])))
        else:
            return None

    def __setitem__(self, key, value, overwrite=True, **kwargs):
        if self._h5 is None:
            raise Exception('No group opened.')

        if value is None:
            if key in self._h5:
                del self._h5[key]
        else:
            from audata.dataset import AUDataset
            AUDataset.new(self, key, value, overwrite=overwrite, **kwargs)

    def __contains__(self, key):
        return self._h5.__contains__(key)

    def new_dataset(self, name, value, **kwargs):
        self.__setitem__(name, value, **kwargs)
