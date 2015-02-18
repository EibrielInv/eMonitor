class emonitor_data():
    name = None
    engine = None
    freestyle = None
    compositor = None
    sequencer = None
    frame_start = None
    frame_end = None
    frame_current = None
    status = None
    data = None

    def array(self):
        params = {
            'name': self.name,
            'engine': self.engine,
            'freestyle': self.freestyle,
            'compositor': self.compositor,
            'sequencer': self.sequencer,
            'frame_start': self.frame_start,
            'frame_end': self.frame_end,
            'frame_current': self.frame_current,
            'status': self.status,
            'data': self.data,
            }
        return params

    def array_update(self):
        params = {}
        array = self.array()
        for key in array:
            if array[key]:
                params[key] = array[key]
        return params

    #def get_data(self, source):
    #    array = self.array()
    #    for key in array:
    #        if source.get(key):
    #            self[key] = source.get(key)
