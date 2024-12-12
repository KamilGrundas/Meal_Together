# Meal together

![Meal together Thumbnail](static/meal_together_thumb.png)

## Introduction

Meal together simplifies group meal ordering by enabling one user (the organizer) to set up a meal session, invite others, and let everyone select their meals and payment methods in a single, streamlined interface. After the order window closes, the organizer receives a complete summary of all orders, costs, and additional notes. This approach removes the hassle of scattered messages, manual cost calculations, and misunderstandings.


## Features

- **User Management & Authentication**  
  - User registration (name, email, password)  
  - Email-based account activation  
  - Password reset via email link  
  - Login/logout functionality  
  - User profile with editable personal data and password changes  

- **Roles & Permissions**  
  - Three user roles: admin, manager, and customer  
  - Admin can define and manage user groups  
  - New users default to the "customer" role  
  - Admin or manager can manage restaurants and menu

- **Navigation & Interface**  
  - A persistent navigation bar visible on every page except login/registration  
  - Links to “Restaurants” (admin/managers), “Meal Sessions” (all), “User Profile” (all), and “Credit Balance” (all)  
  - Display of total amount spent across all sessions at the top of the sessions list

- **Restaurant & Meal Management**  
  - Admin/managers can define restaurants with name, address, and contact number  
  - Add, edit, and remove meals with corresponding prices

- **Meal Sessions**  
  - Any user can create a meal session specifying:
    - Session name 
    - Selected restaurant
    - Delivery time
    - Order deadline  
    - Invited users or groups
  - Session creator can edit session details and is also a participant  
  - Session creator can edit user orders after the deadline if needed  
  - Session invitations sent via email, providing a direct link to place orders  
  - Email notifications for session or order edits, detailing the changes

- **Placing & Editing Orders**  
  - Invited users can place one order per session before the deadline  
  - Choose meals, quantities, and payment method (including “credit”)  
  - Add notes or special instructions to the order  
  - Edit or cancel orders before the deadline  
  - After the deadline, only the session creator can modify orders

- **Order Summaries & Reports**  
  - Session creator can view a comprehensive report of all orders, including:
    - Individual orders with user details, meals, quantities, costs, and notes  
    - An aggregated list of meals with total quantities  
    - Overall total cost of the session
  - After the deadline, an email with a link to the report is sent to the session creator

- **Credit Payment System**  
  - “Credit” as a payment form, allowing deferred settlements  
  - A “Credit Balance” view showing who owes or is owed credit

- **Technologies**  
  - **Django** for the web framework  
  - **Celery** and **background-tasks** for asynchronous operations (e.g., sending emails, delayed tasks)  
  - **PostgreSQL** as the database  
  - **Redis** for caching and as a Celery broker

## Installation & Running

1. **Clone the repository:**
   ```bash
   git clone https://github.com/KamilGrundas/Meal_Together.git
   cd Meal_Together
   ```

2. **Setup and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   Open `http://127.0.0.1:8000` in your browser.

**Note:** Ensure that all required environment variables and credentials (e.g., email service settings) are properly configured in `.env` or Docker configuration files as needed.

## Additional Documentation

Refer to the additional documentation for details on configurations, architectural decisions, and extending the application.

## Contributing

Feel free to fork the repository, submit pull requests, or open issues. Contributions and suggestions are always welcome.