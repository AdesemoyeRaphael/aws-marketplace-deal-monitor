# aws-marketplace-deal-monitor
A serverless AWS Lambda function for monitoring and tracking new product deals on [The Merchant Marketplace](https://merchantmarketplace.com/marketplace).


# [The Merchant Marketplace](https://merchantmarketplace.com/marketplace) Deal Monitor (Lambda Function)

A serverless AWS Lambda function that monitors new deals on [The Merchant Marketplace](https://merchantmarketplace.com/marketplace) and sends real-time WhatsApp notifications using Twilio. It stores and checks previously seen deals in DynamoDB to avoid duplicates and automatically cleans up old records.

---

## ✅ Features

- Fetches latest deals from the Merchant Marketplace API
- Detects and stores only new deals using DynamoDB
- Sends WhatsApp notifications via Twilio when new deals appear
- Automatically deletes old records if database size exceeds 100,000

---

## ⚙️ Environment Variables

Make sure the following environment variables are set in your Lambda configuration:

| Variable         | Description                          |
|------------------|--------------------------------------|
| `TABLE_NAME`     | DynamoDB table name                  |
| `ACCOUNT_SID`    | Twilio Account SID                   |
| `AUTH_TOKEN`     | Twilio Auth Token                    |
| `RECIEVER_NUMBER`| WhatsApp number to send messages to  |
| `SENDER_NUMBER`  | Twilio WhatsApp number               |

---

## 🛠️ Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/adesemoyeraphael/aws-marketplace-deal-monitor.git
   cd aws-marketplace-deal-monitor
   
2. **Install dependencies**
   pip install -r requirements.txt

3. **Deploy to AWS Lambda**
   - Upload your function manually or using SAM/CDK
   - Set required environment variables
   - Schedule with CloudWatch Events (e.g., every hour)

## 🔄 How It Works
1. Lambda fetches current deals from the API
2. Compares them with records in DynamoDB
3. If new deals are found, a WhatsApp alert is sent via Twilio
4. New deals are stored in DynamoDB
5. If total records exceed 100,000, the oldest are deleted
