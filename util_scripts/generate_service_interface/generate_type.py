from JibrelTests.utils.utils import classproperty


class JsonFields(object):
    TYPE = "type"
    ITEMS = "items"
    REF = "$ref"


class JsonTypes(object):
    ARRAY = "array"
    OBJECT = "object"


class_type_template = """
class {type_name}(object):
    @classproperty
    def schema(cls):
        return {type_schema}
"""

def get_ref_class_name(ref_name):
    return ref_name.split('/')[-1]


def generate_class(class_name, class_info):
    if class_info[JsonFields.TYPE] == JsonTypes.ARRAY:
        if JsonFields.REF in class_info[JsonFields.ITEMS]:
            ref = class_info[JsonFields.ITEMS][JsonFields.REF]
            class_info[JsonFields.ITEMS] = get_ref_class_name(ref) + '.schema'




def get_swagger_data(swagger_url):
    import json
    with open('test.json') as file_:
        return json.load(file_)


def generate_types(swagger_data):
    pass


qwe = {
    "Error": {
        "type": "object",
        "properties": {
            "field": {
                "type": "string",
                "example": "NON_FIELD_ERROR"
            },
            "code": {
                "type": "string",
                "example": "ERR_CODE"
            },
            "message": {
                "type": "string",
                "example": "some err text"
            }
        }
    },
    "Errors": {
        "type": "array",
        "items": {
            "$ref": "#/definitions/Error"
        },
        "example": []
    },
    "Status": {
        "properties": {
            "success": {
                "type": "boolean"
            },
            "errors": {
                "$ref": "#/definitions/Errors"
            }
        }
    },
}

if __name__ == "__main__":
    for k, v in qwe.items():
        print(generate_class(k, v))
