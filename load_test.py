import asyncio
import aiohttp
import random
import string
import time
import tkinter as tk
from tkinter import messagebox
from aiohttp import ClientSession
from threading import Thread
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

request_stats = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "response_times": [],
    "status_codes": defaultdict(int)
}

semaphore = None

async def fetch(session, url):
    global request_stats
    async with semaphore:
        try:
            start_time = time.time()
            async with session.get(url) as response:
                end_time = time.time()
                duration = end_time - start_time
                status = response.status
                
                request_stats["total_requests"] += 1
                request_stats["response_times"].append(duration)
                request_stats["status_codes"][status] += 1
                
                if status == 200:
                    request_stats["successful_requests"] += 1
                else:
                    request_stats["failed_requests"] += 1

                print(f"Request sent to {url}. Status code: {status}, Time taken: {duration:.4f} seconds")

        except Exception as e:
            request_stats["failed_requests"] += 1
            print(f"Request to {url} failed: {e}")

async def generate_requests(url, num_requests, use_random_queries):
    async with ClientSession() as session:
        tasks = []
        for _ in range(num_requests):
            if use_random_queries:
                random_path = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
                random_query = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
                full_url = f"{url}/{random_path}?q={random_query}"
            else:
                full_url = url
            tasks.append(fetch(session, full_url))
        
        await asyncio.gather(*tasks)

def run_load_test(url, total_requests, concurrent_requests, use_random_queries):
    global semaphore
    semaphore = asyncio.Semaphore(concurrent_requests)  # Limit concurrency

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(generate_requests(url, total_requests, use_random_queries))
    loop.close()

    summarize_results()
    plot_results()

def summarize_results():
    global request_stats
    total_requests = request_stats["total_requests"]
    successful_requests = request_stats["successful_requests"]
    failed_requests = request_stats["failed_requests"]
    avg_response_time = sum(request_stats["response_times"]) / len(request_stats["response_times"]) if request_stats["response_times"] else 0
    status_code_distribution = dict(request_stats["status_codes"])

    print("\nLoad Test Summary:")
    print(f"Total Requests: {total_requests}")
    print(f"Successful Requests: {successful_requests}")
    print(f"Failed Requests: {failed_requests}")
    print(f"Average Response Time: {avg_response_time:.4f} seconds")
    print(f"Status Code Distribution: {status_code_distribution}")

    summary_message = (
        f"Load Test Summary:\n"
        f"Total Requests: {total_requests}\n"
        f"Successful Requests: {successful_requests}\n"
        f"Failed Requests: {failed_requests}\n"
        f"Average Response Time: {avg_response_time:.4f} seconds\n"
        f"Status Code Distribution: {status_code_distribution}"
    )
    messagebox.showinfo("Load Test Summary", summary_message)

def start_load_test():
    url = url_entry.get()
    try:
        total_requests = int(total_requests_entry.get())
        concurrent_requests = int(concurrent_requests_entry.get())
    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numbers for requests and concurrency.")
        return

    if not url:
        messagebox.showerror("Input Error", "Please enter a valid URL.")
        return

    global request_stats
    request_stats = {
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "response_times": [],
        "status_codes": defaultdict(int)
    }

    use_random_queries = query_option.get() == 1

    start_button.config(state=tk.DISABLED)
    Thread(target=run_load_test, args=(url, total_requests, concurrent_requests, use_random_queries), daemon=True).start()
    messagebox.showinfo("Load Test", f"Load test started on {url} with {total_requests} requests using {concurrent_requests} concurrent requests.")
    start_button.config(state=tk.NORMAL)

def plot_results():
    fig = plt.Figure(figsize=(8, 6))
    ax = fig.add_subplot(111)
    
    response_times = request_stats["response_times"]
    if response_times:
        ax.plot(range(1, len(response_times) + 1), response_times, marker='o', linestyle='-', color='b')
        ax.set_xlabel('Request Number')
        ax.set_ylabel('Response Time (seconds)')
        ax.set_title('Average Response Time per Request')

        canvas = FigureCanvasTkAgg(fig, master=app)
        canvas.draw()
        canvas.get_tk_widget().grid(row=5, columnspan=2, padx=10, pady=10)

app = tk.Tk()
app.title("Load Testing Tool")

tk.Label(app, text="Target URL:").grid(row=0, column=0, padx=10, pady=10)
url_entry = tk.Entry(app, width=50)
url_entry.grid(row=0, column=1, padx=10, pady=10)

tk.Label(app, text="Total Requests:").grid(row=1, column=0, padx=10, pady=10)
total_requests_entry = tk.Entry(app, width=20)
total_requests_entry.grid(row=1, column=1, padx=10, pady=10)

tk.Label(app, text="Concurrent Requests:").grid(row=2, column=0, padx=10, pady=10)
concurrent_requests_entry = tk.Entry(app, width=20)
concurrent_requests_entry.grid(row=2, column=1, padx=10, pady=10)

query_option = tk.IntVar(value=1)
tk.Radiobutton(app, text="Random Query Requests", variable=query_option, value=1).grid(row=3, column=0, padx=10, pady=10)
tk.Radiobutton(app, text="Exact URL Requests", variable=query_option, value=2).grid(row=3, column=1, padx=10, pady=10)

start_button = tk.Button(app, text="Start Load Test", command=start_load_test)
start_button.grid(row=4, columnspan=2, pady=20)

app.mainloop()