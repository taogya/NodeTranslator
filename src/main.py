import logging
import logging.config
from typing import Self

import dearpygui_wrapper as dpg

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s][%(name)s][%(levelname)s] %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG'
    }

})

log = logging.getLogger('main')


class NodeEditorWindow(dpg.Window):
    def build(self, *args, **kwargs) -> Self:
        super().build(*args, **kwargs)

        def input_callback(sender: dpg.DpgTag, app_data: str):
            self.node_editor.update_links(sender, app_data)

        def translater_callback(sender: dpg.DpgTag, app_data: str):
            pass

        self.node_editor: dpg.NodeEditor = dpg.NodeEditor()\
            .add(dpg.Node(label='Input')
                 .add(dpg.NodeAttribute(attribute_type=dpg.NodeAttributeType.OUTPUT)
                      .add(dpg.InputText(callback=input_callback, multiline=True))))\
            .add(dpg.Node(label='Translator')
                 .add(dpg.NodeAttribute(attribute_type=dpg.NodeAttributeType.INPUT)
                      .add(dpg.InputText(callback=translater_callback, multiline=True)))
                 .add(dpg.NodeAttribute(attribute_type=dpg.NodeAttributeType.OUTPUT)
                      .add(dpg.Text())))\
            .add(dpg.Node(label='Output')
                 .add(dpg.NodeAttribute(attribute_type=dpg.NodeAttributeType.INPUT)
                      .add(dpg.Text())))\
            .build(self)

        return self


def main():
    dpg.ViewPort(title='Node Translator', width=800, height=600)\
        .add(NodeEditorWindow(label='Node Editor', width=0, height=0))\
        .build()


if __name__ == '__main__':
    main()
