from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    slug: str
    name: str
    url: str


PRODUCTS: list[Product] = [
    Product(
        slug="estradiol-enanthate",
        name="Estradiol Enanthate (MCT)",
        url="https://astrovials.com/product/estradiol-enanthate/",
    ),
    Product(
        slug="estradiol-valerate",
        name="Estradiol Valerate (MCT)",
        url="https://astrovials.com/product/estradiol-valerate/",
    ),
    Product(
        slug="estradiol-undecylate",
        name="Estradiol Undecylate (MCT)",
        url="https://astrovials.com/product/estradiol-undecylate/",
    ),
    Product(
        slug="estradiol-enanthate-castor",
        name="Estradiol Enanthate (Castor Oil)",
        url="https://astrovials.com/product/estradiol-enanthate-castor/",
    ),
    Product(
        slug="progesterone-100mg-60pcs",
        name="Progesterone 100mg 60pcs",
        url="https://astrovials.com/product/progesterone-100mg-60pcs/",
    ),
]

PRODUCTS_BY_SLUG: dict[str, Product] = {p.slug: p for p in PRODUCTS}
