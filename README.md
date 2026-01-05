# Personal Finance App

This repository contains the SQL schema and setup for a personal finance application. 

## Original Schema

The original schema includes:

- `users` – user accounts with email and password.
- `accounts` – financial accounts linked to users.
- `categories` – income or expense categories.
- `transactions` – financial transactions linked to accounts and categories.
- `transfers` – optional table for transferring funds between accounts.

## Updated Schema with AI Receipt Integration

The updated schema includes new tables to support AI-based receipt parsing:

### New Tables

1. **receipts**  
   Stores uploaded receipt images and metadata extracted by the AI:
   - `transaction_id` (optional link to transaction)
   - `image_url` – path or URL of the receipt
   - `store_name` – detected store
   - `receipt_date` – extracted date
   - `subtotal`, `tax`, `total_amount` – amounts from the receipt
   - `raw_text` – full OCR output
   - `created_at` – timestamp

2. **receipt_items**  
   Stores each item detected on a receipt:
   - `transaction_id` – links to the transaction
   - `name` – item name
   - `quantity` – item quantity
   - `unit_price` – price per item
   - `total_price` – calculated as `quantity * unit_price`
   - `created_at` – timestamp

### Changes to Existing Tables

- `transactions` table now has an optional `receipt_id` column linking to `receipts.id`.
