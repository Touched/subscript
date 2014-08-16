import interface.sourceview

class SubscriptView(interface.sourceview.SourceView):

    def __init__(self, path=None):
        '''
        Constructor
        '''
        super().__init__('python3', 'github', path)

