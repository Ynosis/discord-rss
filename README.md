# RSS Feed Discord Bot into Yeetum Synergy
Forked from vx-underground threat intelligence bot

## Installation

Setup a .env file with your webhooks

```bash
CTI_WEBHOOK=
REUTERS_WEBHOOK=
GOV_FINTEL_WEBHOOK=
RANSOMWARE_WEBHOOK=
STATUS_WEBHOOK=
```
## Run

```bash
pip3 install -r requirements.txt
python3 gno.py
```

## Docker Usage
```bash
docker build --tag rss-webhook-bot .
docker run -d rss-webhook-bot
```
## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)

