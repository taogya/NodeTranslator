import asyncio
import logging
import logging.config
from typing import Self, cast

import dearpygui_wrapper as dpg
from googletrans import Translator

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


class MyNodeEditor(dpg.NodeEditor):
    def link_callback(self, link: dpg.Link):
        self.inject_based_on_out_attr(link.out_attr)\
            .update_callback(link.out_attr.object.tag)

    def delink_callback(self, link: dpg.Link):
        self.inject_based_on_in_attr(link.in_attr)\
            .update_callback(link.in_attr.object.tag)

    def update_callback(self, sender: dpg.DpgTag):
        # ### [sender.parent] -out_link_id-+-> in_attr1 (have callback)
        # ###                              |
        # ###                              +-> in_attr2 (not have callback)
        for link_id in cast(dpg.NodeAttribute, self.manager[sender].parent).links:
            link = cast(dpg.Link, self.manager[link_id])
            callback = link.in_attr.object.kwargs.get('callback')
            if callback:
                user_data = link.in_attr.object.kwargs.get('user_data')
                link.in_attr.object.kwargs['callback'](link.in_attr.object.tag, link.out_attr.object.value, user_data)


class NodeEditorWindow(dpg.Window):
    primary = True

    def build(self, parent: dpg.Object, *args, **kwargs) -> Self:
        super().build(parent, *args, **kwargs)

        def input_callback(sender: dpg.DpgTag, app_data: str):
            print(app_data)
            attr = cast(dpg.NodeAttribute, self.node_editor.manager[sender].parent)
            self.node_editor\
                .inject_based_on_out_attr(attr)\
                .update_callback(sender)

        def translate_callback(sender: dpg.DpgTag, app_data: str, user_data: tuple[str, str]):
            attr = cast(dpg.NodeAttribute, self.node_editor.manager[sender].parent)
            # update input attr
            self.node_editor\
                .inject_based_on_in_attr(attr)
            # get attr
            node = cast(dpg.Node, attr.parent)
            in_attr = cast(dpg.NodeAttribute, node.objects[0])
            out_attr = cast(dpg.NodeAttribute, node.objects[1])
            # update output attr

            async def translate(text, src, dest) -> str:
                translator = Translator()
                translated = await translator.translate(text, src=src, dest=dest)
                return translated.text

            def translate_sync(text, src, dest):
                return asyncio.run(translate(text, src, dest))

            out_attr.object.value = translate_sync(in_attr.object.value, src=user_data[0], dest=user_data[1])
            self.node_editor.update_callback(out_attr.object.tag)

        self.node_editor: MyNodeEditor = MyNodeEditor()\
            .add(dpg.Node(label='EN Input', pos=(0, 0))
                 .add(dpg.NodeAttribute(attribute_type=dpg.NodeAttributeType.OUTPUT, tag='out_attr_1')
                      .add(dpg.InputText(callback=input_callback, multiline=True, always_overwrite=True, width=300, height=100))))\
            .add(dpg.Node(label='EN to JP', pos=(400, 0))
                 .add(dpg.NodeAttribute(attribute_type=dpg.NodeAttributeType.INPUT, tag='en_to_ja_in_attr_1')
                      .add(dpg.InputText(callback=translate_callback, user_data=('en', 'ja'), multiline=True, readonly=True, width=300, height=100)))
                 .add(dpg.NodeAttribute(attribute_type=dpg.NodeAttributeType.OUTPUT, tag='en_to_ja_out_attr_1')
                      .add(dpg.InputText(callback=input_callback, multiline=True, readonly=True, width=300, height=100))))\
            .add(dpg.Node(label='JP to EN', pos=(800, 0))
                 .add(dpg.NodeAttribute(attribute_type=dpg.NodeAttributeType.INPUT, tag='ja_to_en_in_attr_1')
                      .add(dpg.InputText(callback=translate_callback, user_data=('ja', 'en'), multiline=True, readonly=True, width=300, height=100)))
                 .add(dpg.NodeAttribute(attribute_type=dpg.NodeAttributeType.OUTPUT, tag='ja_to_en_out_attr_1')
                      .add(dpg.InputText(callback=input_callback, multiline=True, readonly=True, width=300, height=100))))\
            .add(dpg.Node(label='JP Input', pos=(0, 300))
                 .add(dpg.NodeAttribute(attribute_type=dpg.NodeAttributeType.OUTPUT, tag='out_attr_2')
                      .add(dpg.InputText(callback=input_callback, multiline=True, always_overwrite=True, width=300, height=100))))\
            .add(dpg.Node(label='JP to EN', pos=(400, 300))
                 .add(dpg.NodeAttribute(attribute_type=dpg.NodeAttributeType.INPUT, tag='ja_to_en_in_attr_2')
                      .add(dpg.InputText(callback=translate_callback, user_data=('ja', 'en'), multiline=True, readonly=True, width=300, height=100)))
                 .add(dpg.NodeAttribute(attribute_type=dpg.NodeAttributeType.OUTPUT, tag='ja_to_en_out_attr_2')
                      .add(dpg.InputText(callback=input_callback, multiline=True, readonly=True, width=300, height=100))))\
            .add(dpg.Node(label='EN to JP', pos=(800, 300))
                 .add(dpg.NodeAttribute(attribute_type=dpg.NodeAttributeType.INPUT, tag='en_to_ja_in_attr_2')
                      .add(dpg.InputText(callback=translate_callback, user_data=('en', 'ja'), multiline=True, readonly=True, width=300, height=100)))
                 .add(dpg.NodeAttribute(attribute_type=dpg.NodeAttributeType.OUTPUT, tag='en_to_ja_out_attr_2')
                      .add(dpg.InputText(callback=input_callback, multiline=True, readonly=True, width=300, height=100))))\
            .build(self)

        self.node_editor.link_callback(dpg.Link('out_attr_1', 'en_to_ja_in_attr_1')
                                       .build(self.node_editor, self.node_editor.manager))
        self.node_editor.link_callback(dpg.Link('en_to_ja_out_attr_1', 'ja_to_en_in_attr_1')
                                       .build(self.node_editor, self.node_editor.manager))
        self.node_editor.link_callback(dpg.Link('out_attr_2', 'ja_to_en_in_attr_2')
                                       .build(self.node_editor, self.node_editor.manager))
        self.node_editor.link_callback(dpg.Link('ja_to_en_out_attr_2', 'en_to_ja_in_attr_2')
                                       .build(self.node_editor, self.node_editor.manager))

        return self


class MyViewPort(dpg.ViewPort):
    def build(self, minimized=False, maximized=False, **kwargs):
        with dpg.dpg_org.font_registry():
            default_font = dpg.dpg_org.add_font('NotoSansJP-VariableFont_wght.ttf', 16)
            dpg.dpg_org.add_font_range_hint(dpg.dpg_org.mvFontRangeHint_Japanese, parent=default_font)
            dpg.dpg_org.bind_font(default_font)
        return super().build(minimized, maximized, **kwargs)


def main():
    MyViewPort(title='Node Translator', width=1280, height=720)\
        .add(NodeEditorWindow(label='Node Editor'))\
        .build()


if __name__ == '__main__':
    main()
