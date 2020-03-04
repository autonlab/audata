import h5py as h5


class AUGroup:
    def __init__(self, af, path):
        # if not isinstance(af, AUFile):
        #     raise Exception('Invalid AUFile file.')

        self._af = af

        if path != '' and (path not in self._af._f or not isinstance(self._af._f[path], h5.Group)):
            raise Exception('Path {} is not a group in {}'.format(path, self._af._f.filename))

        self._path = path
        self._root = af._f[path] if path != '' else af._f

    def list(self):
        attrs = list(self._root.attrs)
        others = list(self._root)
        groups = [g for g in others if isinstance(self._root[g], h5.Group)]
        datasets = [d for d in others if isinstance(self._root[d], h5.Dataset)]
        return {
            'attributes': attrs,
            'groups': groups,
            'datasets': datasets
        }

    def __repr__(self):
        lines = []
        l = self.list()
        if self._path == '':
            lines.append('<ROOT>')
        else:
            lines.append(self._path)

        for t in l['attributes']:
            lines.append('  [A] {}'.format(t))
        for t in l['groups']:
            lines.append('  [G] {}'.format(t))
        for t in l['datasets']:
            lines.append('  [D] {}'.format(t))
        return '\n'.join(lines)

    def __str__(self):
        return self.__repr__()
