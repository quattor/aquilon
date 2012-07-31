{
    "interfaces": {
        "mgmt0": {
            "ip": {
                "4.2.20.5": ""
            },
            "type": "loopback"
        },
        "vlan100": {
            "ip": {
                "4.2.20.6": "hsrp",
                "4.2.20.9": ""
            },
            "type": "oa"
        },
        "vlan210": {
            "ip": {
                "4.2.20.7": ""
            },
            "type": "oa"
        },
        "vlan310": {
            "ip": {
                "4.2.20.8": ""
            },
            "type": "oa"
        },
        "vlan500": {
            "ip": {
                "4.2.20.10": ""
            },
            "type": "oa"
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
