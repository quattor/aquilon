{
    "interfaces": {
        "mgmt0": {
            "ip": {
                "4.2.20.5": ""
            },
            "type": "physical"
        },
        "vlan100": {
            "ip": {
                "4.2.20.6": "hsrp",
                "4.2.20.9": ""
            },
            "type": "virtual"
        },
        "vlan210": {
            "ip": {
                "4.2.20.7": ""
            },
            "type": "virtual"
        },
        "vlan310": {
            "ip": {
                "4.2.20.8": ""
            },
            "type": "virtual"
        },
        "vlan500": {
            "ip": {
                "4.2.20.10": ""
            },
            "type": "virtual"
        }
    },
    "model": "ws-c2960-48tt-l",
    "router_ips": [
        "4.2.20.6"
    ],
    "tags": [
        "T1",
        "T2"
    ],
    "vendor": "cisco"
}
