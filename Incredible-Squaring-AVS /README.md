# Zellular Squaring Task Manager

This project is a decentralized task manager that uses [Zellular](https://docs.zellular.xyz) to post and process squaring tasks. Users can submit a number to be squared, and the result is computed and stored in a local SQLite database once the transaction is finalized by Zellular.

## Features

- **Task Posting**: Users can submit a number to be squared, and the task is posted to Zellular.
- **Transaction Verification**: All transactions are verified using ECDSA signatures.
- **Task Processing**: The system continuously listens for finalized transactions from Zellular, squares the submitted numbers, and stores the results in a database.
- **Result Storage**: The squared results are stored in an SQLite database for future reference.
- **Decentralized Sequencing**: All tasks are managed and finalized by Zellular, ensuring fault tolerance and correct ordering.

## Prerequisites

- Python 3.x
- Zellular SDK (installed via `pip install zellular`)
- SQLite (built into Python)
- Flask (installed via `pip install flask`)
- Flask SQLAlchemy (installed via `pip install flask_sqlalchemy`)
- ECDSA Library (installed via `pip install ecdsa`)
- Requests Library (installed via `pip install requests`)

## Installation

1. **Clone the Repository**:

    ```bash
    git clone https://github.com/your-repo/cellular-squaring-task-manager.git
    cd cellular-squaring-task-manager
    ```

2. **Install Dependencies**:

    Install the required Python libraries:

    ```bash
    pip install -r requirements.txt
    ```

    If you don't have a `requirements.txt`, use the following to install the needed packages:

    ```bash
    pip install flask flask_sqlalchemy ecdsa requests zellular
    ```

3. **Set Up the SQLite Database**:

    The database will be created automatically when the application starts. Ensure that the app is pointed to the correct SQLite file in the `app.config['SQLALCHEMY_DATABASE_URI']`.

## Usage

### Posting a Task

1. Run the Flask application:

    ```bash
    python app.py
    ```

2. To post a new task (number to be squared), send a POST request to the `/post_task` endpoint.

    Example:

    ```bash
    curl -X POST http://localhost:5000/post_task \
         -d "public_key=<sender_public_key>" \
         -d "task_id=123" \
         -d "number_to_be_squared=5" \
         -d "signature=<signature>"
    ```

    This will square the number `5` and post the task to Zellular.

### Processing Tasks

The application continuously listens for finalized tasks from Zellular. When a task is finalized, the system verifies the transaction and saves the squared result to the SQLite database.

### Checking Results

You can check the results of the squared tasks by directly accessing the `squared.db` database using an SQLite browser or executing SQLite queries.

### Example of Data in the Database:

| ID  | Number to be Squared | Squared Result |
| --- | -------------------- | -------------- |
| 1   | 5                    | 25             |
| 2   | 7                    | 49             |

## Project Structure

```plaintext
.
├── app.py                    # Main application file
├── squared.db                 # SQLite database (auto-generated)
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
```

## API Endpoints

### POST `/post_task`

Submit a new number to be squared.

#### Parameters:

- `public_key` (string): Base64 encoded public key of the sender.
- `task_id` (string): Unique task ID.
- `number_to_be_squared` (int): The number that needs to be squared.
- `signature` (string): Base64 encoded signature of the transaction.

#### Example Request:

```bash
curl -X POST http://localhost:5000/post_task \
     -d "public_key=<sender_public_key>" \
     -d "task_id=123" \
     -d "number_to_be_squared=5" \
     -d "signature=<signature>"
```

#### Example Response:

```json
{
  "message": "Task successfully posted",
  "task_id": "123"
}
```

### Background Task Processing

The system continuously listens for finalized transactions from Zellular and processes each task by saving the squared result in the database.

## Conclusion

This project demonstrates how to integrate Zellular into a decentralized task processing system. It verifies transactions, posts tasks to Zellular, processes the finalized tasks, and stores the squared results in an SQLite database. You can extend the functionality to handle more complex workflows or tasks as needed.

## License

This project is open-source and available under the MIT License.