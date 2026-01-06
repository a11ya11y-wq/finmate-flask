
MAX_BUDGET_PER_USER = 5

MAX_CATEGORIES_PER_USER = 10

VALID_PERIODS = ('all', 'week', 'month')

MAX_CATEGORIES_PER_USER = 10

ALLOWED_ICONS = [
        'bi-bag-fill',
        'bi-cart-fill',
        'bi-cup-hot-fill',
        'bi-basket2-fill',
        'bi-house-door-fill',
        'bi-lightning-fill',
        'bi-wifi',
        'bi-car-front-fill',
        'bi-bus-front-fill',
        'bi-fuel-pump-fill',
        'bi-controller',
        'bi-film',
        'bi-heart-pulse-fill',
        'bi-mortarboard-fill',
        'bi-piggy-bank-fill',
        'bi-wallet-fill',
        'bi-gift-fill',
        'bi-tools',
        'bi-airplane-fill',
        'bi-tag-fill',
        'bi-question-circle-fill'
    ]

ALLOWED_AVATARS = [
        'avatars/default/default.svg',
        'avatars/default/1.svg',
        'avatars/default/2.svg',
        'avatars/default/3.svg',
        'avatars/default/4.svg',
        'avatars/default/5.svg',
        'avatars/default/6.svg',
        'avatars/default/7.svg',
        'avatars/default/8.svg',
        'avatars/default/9.svg',
    ]


DEFAULT_CATEGORIES = [
    {
        "name": "Food",
        "mcc_code": "5411, 5812, 5814, 5499",
        "icon": "bi-cup-hot-fill"
    },
    {
        "name": "Transport",
        "mcc_code": "5541, 5542, 4121, 4111, 4784",
        "icon": "bi-car-front-fill"
    },
    {
        "name": "Entertainment",
        "mcc_code": "5813, 7832, 7922, 7996, 7999",
        "icon": "bi-controller"
    },
    {
        "name": "Shopping",
        "mcc_code": "5311, 5691, 5732, 5912, 5941, 5942",
        "icon": "bi-bag-fill"
    },
    {
        "name": "Utilities",
        "mcc_code": "4900, 4814, 4899",
        "icon": "bi-lightning-fill"
    },
    {
        "name": "Salary",
        "mcc_code": None,
        "icon": "bi-wallet-fill"
    },
    {
        "name": "Uncategorized",
        "mcc_code": None,
        "icon": "bi-tag-fill"
    }
]