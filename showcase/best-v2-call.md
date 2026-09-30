# Best v2 call: Slice Street Cafe pizza order (Bolna)

Agent v2 (locked config), 155 s, scored 8/11 on the locked rubric (checks 1-11).
Personal details in this copy (name, address, phone number) are replaced with dummy ones. The agent's wording and the structure of each turn are unchanged.

## What it did right
- Prices in rupees, never "Rs"; read-back shows subtotal, delivery and total (409 + 40 = 449).
- Collected all five address parts one at a time, then read the address back.
- Read the phone number back digit by digit and got a yes.

## Misses on the locked rubric
- Did not ask the caller to confirm the address after reading it back (C11).
- Jumped in twice (C06 allows at most 1).
- Asked for house number and street twice (C05), because the caller gave a landmark first.

## Transcript
```
assistant: Namaste! Main Slice Street Cafe se Priya bol rahi hoon. Aap kya order karna chahenge aaj?
user: If you record your
assistant:  Sorry, I didn't catch that. Could you please tell me what you'd like to order from our menu?
user: I would like to have one medium Margherita pizza. Along with that, I need Sprite as well.
assistant:  Great choice! One medium Margherita pizza and a Sprite. Could you please share your delivery address with house number, building, street, area, and a landmark?
user: I've seen Koramangala.
user: Uh, and, uh, it's, uh, Sai Residency.
assistant:  Thanks! Could you please tell me the house or flat number and the street name too, so the rider finds you easily?
user: It's in an-
assistant: Just to confirm, could
user: It's right to the Forum Mall.
assistant:  Thanks for that! Could you please provide the house or flat number and the street name as well? That will help the rider find you easily.
user: It's 12. Y- yes, it's 12.
assistant:  Got it, house number 12. Could you please tell me the street name too?
user: All right. 5th Cross Road.
assistant:  Thanks! So the address is house number 12, 5th Cross Road, Sai Residency, Koramangala, near Forum Mall. Now, may I have your phone number for the order?
user: 98765 43210.
assistant:   Let me read back your phone number: 9 8 7 6 5 4 3 2 1 0. Is that correct?
user: Yes.
assistant:   Would you like to pay by cash or UPI on delivery?
user: UPI handle, [name].
assistant:   Got it, UPI payment with the handle [name]. Would you like to add a tip for the delivery person?
user: No.
assistant: Perfect! Here's your order: one medium Margherit
user: What's on your phone?
assistant:  Your order is one medium Margherita pizza for 349 rupees and one Sprite for 60 rupees. The subtotal is 409 rupees, delivery charge is 40 rupees, so the total comes to 449 rupees. Does everything look good?
user: Yes.
assistant: Thank you for your order! Your pizza and Sprite will be delivered in about 35- 40 minutes. Have a great day and enjoy your meal!
```
