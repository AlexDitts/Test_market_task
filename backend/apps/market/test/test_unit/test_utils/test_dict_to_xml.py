from lxml.etree import tostring

from apps.market.utils import dict_to_xml


class TestYandexFeedFile:
    def test__simple_dict_data(self) -> None:
        data = {'key': 'value', 'attrib': {'attr_name': 'attr_value'}}
        result = dict_to_xml(data).getchildren()[0]
        assert result.text == 'value'

    def test__count__items(self) -> None:
        data = {'key': 'value', 'key1': 'value1'}
        result = len(dict_to_xml(data, parent=None).getchildren())
        assert result == 2

    def test__nested_dict_data(self) -> None:
        data = {'key': {'key1': 'value1'}}
        xml_data = dict_to_xml(data)
        result = xml_data.find('key').getchildren()[0]
        assert result.tag == 'key1'
        assert result.text == 'value1'

    def test__nested_list_data(self) -> None:
        data = {'key': [{'key1': 'value1'}, {'key2': 'value2'}]}
        xml_data = dict_to_xml(data)
        elements_of_list = xml_data.find('key').getchildren()
        assert len(elements_of_list) == 2
        assert elements_of_list[0].tag == 'key1'
        assert elements_of_list[1].tag == 'key2'
        assert elements_of_list[0].text == 'value1'
        assert elements_of_list[1].text == 'value2'

    def test__xml_attributes(self):
        data = {'key': {'key1': 'value1', 'attrib': {'id': '123', 'name': 'attr_name'}}}
        xml_data = dict_to_xml(data)
        result = xml_data.find('key')
        assert result.attrib['id'] == '123'
        assert result.attrib['name'] == 'attr_name'



