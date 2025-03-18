import logging.config
from typing import Any

import dearpygui.dearpygui as dpg
import trace_logger as logger

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

log = logger.TraceLogger('main')


# for func in dir(dpg):
#     attr = getattr(dpg, func)
#     if attr.__class__ != '__class__' and callable(attr):
#         setattr(dpg, func, log.func_trace(attr))

DpgTag = int | str


class Object:
    is_instance = False
    generator: staticmethod
    customs: dict[str, Any] = {}

    def __init__(self, *args, **kwargs):
        if not self.is_instance:
            raise TypeError(f'Cannot instantiate abstract class {self.__class__.__name__}')
        self.args = args
        self.kwargs = kwargs

    @property
    def value(self) -> Any:
        return dpg.get_value(self.tag)

    @value.setter
    def value(self, value: Any):
        dpg.set_value(self.tag, value)

    def build(self, parent: DpgTag, *args, **kwargs) -> 'Object':
        self.parent = parent
        self.tag = self.generator(*self.args, parent=self.parent, **self.customs, **self.kwargs)
        return self


class Container(Object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.objects: list[Object] = []

    def add(self, obj: 'Object') -> 'Container':
        self.objects.append(obj)

        return self

    def build(self, parent: DpgTag, *args, **kwargs) -> 'Container':
        self.parent = parent
        self.tag = self.generator(*self.args, parent=self.parent, **self.customs, **self.kwargs)
        for obj in self.objects:
            obj.build(self.tag, *args, **kwargs)
        return self


class OnceContainer(Container):
    def add(self, obj: 'Object') -> 'OnceContainer':
        if self.objects:
            raise ValueError(f'{self.__class__.__name__} can have only one object.')
        super().add(obj)
        return self

    @property
    def object(self) -> Object:
        if not self.objects:
            raise ValueError(f'{self.__class__.__name__} has no object.')
        return self.objects[0]


class Text(Object):
    is_instance = True
    generator = staticmethod(dpg.add_text)


class InputText(Object):
    is_instance = True
    generator = staticmethod(dpg.add_input_text)


class NodeAttribute(OnceContainer):
    is_instance = True
    generator = staticmethod(dpg.add_node_attribute)
    customs: dict[str, Any] = {'attribute_type': dpg.mvNode_Attr_Static}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.links: dict[DpgTag, list['NodeAttribute']] = {}

    def build(self, parent: DpgTag, attr_manager: dict[DpgTag, 'NodeAttribute'], *args, **kwargs) -> 'NodeAttribute':
        super().build(parent, *args, **kwargs)
        attr_manager[self.tag] = self
        return self

    def add_link(self, link_id: DpgTag, output_attr: 'NodeAttribute'):
        self.links.setdefault(link_id, []).append(output_attr)


class OutputAttribute(NodeAttribute):
    is_instance = True
    customs: dict[str, Any] = {'attribute_type': dpg.mvNode_Attr_Output}


class InputAttribute(NodeAttribute):
    is_instance = True
    customs: dict[str, Any] = {'attribute_type': dpg.mvNode_Attr_Input}


class StaticAttribute(NodeAttribute):
    is_instance = True
    customs: dict[str, Any] = {'attribute_type': dpg.mvNode_Attr_Static}


class Node(Container):
    is_instance = True
    generator = staticmethod(dpg.add_node)


class NodeEditor(Container):
    is_instance = True
    generator = staticmethod(dpg.add_node_editor)


class Window:
    label = 'Node Editor'
    width = 0
    height = 0

    def __init__(self, primary: bool = False, **kwargs):
        self.tag = dpg.add_window(label=self.label,
                                  width=self.width,
                                  height=self.height,
                                  **kwargs)
        dpg.set_primary_window(self.tag, primary)
        self.attrs: dict[DpgTag, NodeAttribute] = {}

    def build(self) -> 'Window':

        def link_callback(sender, app_data):
            link_id = dpg.add_node_link(*app_data, parent=sender)
            input_attr = self.attrs[app_data[0]]
            output_attr = self.attrs[app_data[1]]
            input_attr.add_link(link_id, output_attr)
            output_attr.object.value = input_attr.object.value

        def delink_callback(sender, app_data):
            dpg.delete_item(app_data)
            for attr in self.attrs.values():
                for link_id in attr.links.keys():
                    if link_id == app_data:
                        del attr.links[link_id]
                        return

        def input_callback(sender: DpgTag, app_data: str):
            attr = [attr for attr in self.attrs.values() if attr.object and attr.object.tag == sender] or None
            if attr is None:
                return
            out_attrs = [out_attr
                         for out_attrs in attr[0].links.values()
                         for out_attr in out_attrs]
            for out_attr in out_attrs:
                out_attr.object.value = app_data

        self.node_editor = NodeEditor(callback=link_callback, delink_callback=delink_callback)\
            .add(Node(label='Input')
                 .add(OutputAttribute()
                      .add(InputText(callback=input_callback, multiline=True))))\
            .add(Node(label='Output 1')
                 .add(InputAttribute()
                      .add(Text())))\
            .add(Node(label='Output 2')
                 .add(InputAttribute()
                      .add(Text())))\
            .build(self.tag, attr_manager=self.attrs)

        return self


class ViewPort:
    title = 'Node Translator'
    width = 800
    height = 600

    def __init__(self, create_kwargs={}, setup_kwargs={}, show_kwargs={}):
        dpg.create_context()
        dpg.create_viewport(title=self.title,
                            width=self.width,
                            height=self.height,
                            **create_kwargs)
        dpg.setup_dearpygui(**setup_kwargs)
        dpg.show_viewport(**show_kwargs)

        self.__windows = []

    def add_window(self, window: Window) -> 'ViewPort':
        self.__windows.append(window)
        return self

    def run(self):
        dpg.start_dearpygui()

    def __del__(self):
        dpg.destroy_context()


def main():
    ViewPort()\
        .add_window(Window(primary=True).build())\
        .run()


if __name__ == '__main__':
    main()
