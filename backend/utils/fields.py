import json

from django import forms
from django.core.validators import (
    FileExtensionValidator,
    get_available_image_extensions,
)
from django.db.models import FileField
from django.utils.safestring import mark_safe


def validate_image_or_svg_file_extension(value: str) -> FileExtensionValidator:
    allowed_extensions = get_available_image_extensions() + ["svg"]
    return FileExtensionValidator(allowed_extensions=allowed_extensions)(value)


class ImageOrSVGField(FileField):
    default_validators = [validate_image_or_svg_file_extension]

    def pre_save(self, model_instance, add):
        return super().pre_save(model_instance=model_instance, add=add)


class DadataWidget(forms.TextInput):
    """
    Base class for dadata jquery widgets

    Subclass and define widget_type. It can be
    ('NAME', 'PARTY', 'ADDRESS', 'BANK', 'EMAIL')
    see https://dadata.ru/suggestions/usage/
    """

    # subclasses should override this props
    jscode = "console.log(suggestion);"
    widget_type = None

    options = {
        "count": 5,
        "input_id": "id_name",
        "type": widget_type,
        "linked_fields": {},  # should be a map like { '<dadata_field_name>' : '<input_id>' }
    }

    def start_jscript(self, options):
        options["token"] = DaDataCredentials.get_solo().token
        jscode = (
            """
                    <script type="text/javascript">
                    (function dadataInput () {
                    const mapper = %(linked_fields)s;
                    const input = document.querySelector('#%(input_id)s')
                    const div = input.parentElement
                    div.parentElement.classList.add('suggestions-form-container')
                    div.style.position = 'relative'
                    div.style.width = 'min-content'
                    const suggestionsDiv = document.createElement('div')
                    suggestionsDiv.style.display = 'none'
                    suggestionsDiv.style.textWrap = 'nowrap'
                    suggestionsDiv.className = 'suggestions-drop-list'
                    div.append(suggestionsDiv);
                    const createSuggestionsChild = ({value, data}) => {
                        const el = document.createElement('div')
                        el.className = ''
                        el.textContent = value
                        el.style.cursor = 'pointer'
                        el.style.paddingBlock = '4px'
                        el.addEventListener('click', () => {
                            input.value = value
                            Object.entries(mapper).forEach(([key, variable]) => {
                                const node = document.querySelector(`#${key}`)
                                const content = data[variable]
                                if (node) {
                                    node.value = content ? content : ''
                                }
                            })
                           suggestionsDiv.style.display = 'none'
                        })
                        suggestionsDiv.append(el)
                    }
                    var url = 'https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/%(type)s'
                    function debounce(func, ms) {
                        let timeout;
                        return function() {
                          clearTimeout(timeout);
                          timeout = setTimeout(() => func.apply(this, arguments), ms);
                        };
                      }
                    const postData = async (query) => {
                        const count = %(count)s
                        const locations = [
                            {
                                "country_iso_code": "*"
                            }
                        ]
                        const response = await fetch(url, {
                            method: 'POST',
                            mode: 'cors',
                            headers: {
                                'Content-Type': 'application/json',
                                'Accept': 'application/json',
                                'Authorization': 'Token %(token)s'
                            },
                            body: JSON.stringify({query, count, locations})
                        })
                        return response.json()
                    }
                    let queryies = []
                    input.addEventListener('focus', () => {
                        suggestionsDiv.style.display = 'flex'
                        if (!queryies.length) suggestionsDiv.innerHtml = '<div>пока ничего нет</div>'
                    })
                    input.addEventListener('blur', () => {
                    setTimeout(() => {suggestionsDiv.style.display = 'none'}, 100)
                    })
                    input.addEventListener('input', debounce(async ({target}) => {
                        if (target.value.length > 1) {
                            const { suggestions } = await postData(target.value)
                            queryies = suggestions.map(item => item)
                            suggestionsDiv.textContent = ''
                            queryies.forEach(item => createSuggestionsChild(item))
                        }
                    }, 700))
                    
                })()
                """
            % options
        )
        return jscode

    def close_jscript(self):
        return "</script>"

    def render_jscript(self, options, inner_js=None):
        return self.start_jscript(options) + inner_js + self.close_jscript()

    def get_options(self):
        options = dict(self.options)
        if self.widget_type:
            options["type"] = self.widget_type
        return options

    def render(self, name, value, attrs=None, renderer=None):
        jscode = self.jscode
        options = self.get_options()
        attrs = self.build_attrs(attrs)
        attrs["autocomplete"] = "off"

        if self.widget_type:
            id_ = attrs.get("id", None)

            linked_fields_ = self.attrs.get("dadata_linked", None)
            if linked_fields_:
                options["linked_fields"] = json.dumps(linked_fields_)
            options["input_id"] = id_
            if jscode:
                jscode = self.render_jscript(options, jscode)

        s = str(super(DadataWidget, self).render(name, value, attrs))
        s += jscode
        return mark_safe(s)

    class Media:
        js = ("https://dadata.ru/static/js/lib/jquery.suggestions-15.8.min.js",)

        css = {
            "all": (
                "https://dadata.ru/static/css/lib/suggestions-15.8.css",
                "dadata/css/common.css",
            )
        }


class DadataAddressWidget(DadataWidget):
    """
    Russian address select input.
    Uses dadata.ru JQuery plugin for suggestions.
    """

    widget_type = "address"
    jscode = "console.log('address');"


class DadataOrgWidget(DadataWidget):
    """
    Russian organisation select input.
    Uses dadata.ru JQuery plugin for suggestions.
    """

    widget_type = "party"
    jscode = "console.log('party');"


class DadataBankWidget(DadataWidget):
    """
    Russian bank select input.
    Uses dadata.ru JQuery plugin for suggestions.
    """

    widget_type = "bank"
    jscode = "console.log('bank');"
