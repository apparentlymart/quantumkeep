
from quantumkeep.schema import Schema, Attribute, PrimitiveType


# The schema for defining schemas
meta_schema = Schema()

meta_schema.add_object_type("TypeRef", ())
type_ref_type = meta_schema.object_type("TypeRef")
type_ref_type.attributes = (
    Attribute('type_type', PrimitiveType.string),
    Attribute('name', PrimitiveType.string),
    Attribute('key_type', type_ref_type),
    Attribute('value_type', type_ref_type),
)
meta_schema.add_object_type("Attribute", (
    Attribute("key", PrimitiveType.string),
    Attribute("caption", PrimitiveType.string),
    Attribute("differ", PrimitiveType.string),
    Attribute("type", type_ref_type),
))

meta_schema.add_object_type("ObjectType", (
    Attribute("name", PrimitiveType.string),
    Attribute("attributes", meta_schema.list_type(
        meta_schema.object_type("Attribute")
    ))
))

meta_schema.add_object_type("Container", (
    Attribute("name", PrimitiveType.string),
    Attribute("item_type", type_ref_type),
    Attribute("name", PrimitiveType.string),
))
