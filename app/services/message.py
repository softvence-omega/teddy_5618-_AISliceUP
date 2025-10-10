import os
import asyncio
import requests
from collections import defaultdict
from openai import OpenAI
from dotenv import load_dotenv
from app.core.config import API_BASE_URL

load_dotenv(override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

API_URL = f"{API_BASE_URL}/groupTransaction/getGroups/{{}}"
def fetch_group_data(user_id):
    response = requests.get(API_URL.format(user_id))
    response.raise_for_status()
    return response.json()["data"]

def generate_llm_summary(user_id):
    groups = fetch_group_data(user_id)
    summary_messages = []

    for group in groups:
        group_name = group["groupName"]
        group_id = group["groupId"]
        members = group["groupMembers"] + [group["ownerEmail"]]
        
        balances = defaultdict(float)
        for expense in group.get("groupExpenses", []):
            paid_by = expense["paidBy"]["memberEmail"]
            amount = expense["paidBy"]["amount"]
            share_members = expense["shareWith"]["members"]
            share_count = len(share_members)
            share_amount = amount / share_count if share_count else 0

            for member in share_members:
                balances[member] -= share_amount
            balances[paid_by] += amount

        balance_info = ", ".join([f"{m}: {b:.2f}" for m, b in balances.items()])

        system_prompt = (
            "You are **Teddy**, a witty yet professional finance assistant.\n\n"
            "Goal:\n"
            "Turn dry group expense data into short, human-friendly insights and summaries that sound natural, empathetic, and occasionally funny.\n\n"
            "Input:\n"
            "- Group name, owner, members, and all expenses (each with paidBy, amount, shared members, and optional notes).\n\n"
            "Tasks:\n"
            "1. Calculate how much each person owes or is owed.\n"
            "2. Summarize clearly:\n"
            "   - Who owes whom and how much.\n"
            "   - Who should receive money.\n"
            "   - Who is settled.\n"
            "3. Add a short emotional or humorous reflection line based on spending behavior:\n"
            "   - If one member paid a lot more → playful line like 'You're the group's unofficial sponsor!'\n"
            "   - If all are settled → cheerful closure like 'Everyone’s balanced — peace restored!'\n"
            "   - If debts are mixed → friendly nudge like 'Looks like a few IOUs still floating around.'\n"
            "4. Keep everything under 2–3 short lines.\n\n"
            "Tone & Style:\n"
            "- Friendly, conversational, and concise.\n"
            "- Use light humor and emojis where appropriate (💸, 🤝, 😅, 🎉, etc.).\n"
            "- Never sound robotic or overly formal.\n"
            "- Focus on clarity first, personality second.\n\n"
            "Example outputs:\n"
            "💰 Bangkok Trip: Shakil owes Rezwan $120. Everyone else is settled. Note: Dinner at Italian restaurant.\n"
            "😂 Owe $500 but only collecting $20? You’re basically the group’s sponsor!\n"
            "🎉 Art Gallery: Everyone’s square — no drama this time!"
        )


        full_prompt = (
            f"Group '{group_name}' balances: {balance_info}. "
            f"Members: {', '.join(members)}. "
            "Extract member names from email addresses. "
            "Generate a short, 2-3 line human-readable summary of who owes whom, "
            "who should receive money, and who is settled. Include notes in one line."
        )

        # Use acreate for async call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )

        summary = response.choices[0].message.content.strip()
        summary_messages.append({
            "groupId": group_id,
            "groupName": group_name,
            "summary": summary
        })

    return summary_messages
