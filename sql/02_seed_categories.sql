-- Insert some common spending categories 
INSERT INTO categories (category_name, description) VALUES 
    ('Groceries', 'Food and household items'), 
    ('Dining', 'Restaraunts and takeout'),
    ('Transportation', 'Gas, uber, public transit'),
    ('Shopping', 'Retail purchases online or in person'),
    ('Entertainment', 'Movies, concerts, Events'),
    ('Bills', 'Utilities and insurance costs'),
    ('Travel', 'Hotels, flights, vacation'),
    ('Subscriptions', 'Streaming services and memberships'),
    ('Other', 'Miscellaneous expenses')
ON CONFLICT (category_name) DO NOTHING;
