#ifndef AFINA_CONCURRENCY_EXECUTOR_H
#define AFINA_CONCURRENCY_EXECUTOR_H

#include <chrono>
#include <condition_variable>
#include <functional>
#include <memory>
#include <mutex>
#include <queue>
#include <string>
#include <thread>

namespace Afina {
namespace Concurrency {

class Executor;
void perform(Executor *executor);

/**
 * # Thread pool
 */
class Executor {
private:
    enum class State {
        // Threadpool is fully operational, tasks could be added and get executed
        kRun,

        // Threadpool is on the way to be shutdown, no ned task could be added, but existing will be
        // completed as requested
        kStopping,

        // Threadppol is stopped
        kStopped
    };

    std::size_t low_watermark;
    std::size_t hight_watermark;
    std::size_t max_queue_size;
    std::chrono::duration<std::size_t, std::milli> idle_time;
    std::size_t sleeping_workers;

    // No copy/move/assign allowed
    Executor(const Executor &) = delete;
    Executor(Executor &&) = delete;
    Executor &operator=(const Executor &) = delete;
    Executor &operator=(Executor &&) = delete;

    /**
     * Main function that all pool threads are running. It polls internal task queue and execute tasks
     */
    friend void perform(Executor *executor);

    /**
     * Mutex to protect state below from concurrent modification
     */
    std::mutex mutex;

    /**
     * Conditional variable to await new data in case of empty queue
     */
    std::condition_variable empty_condition;

    /**
     * Number of actual threads that perorm execution
     */
    std::size_t running_threads;

    /**
     * Task queue
     */
    std::deque<std::function<void()>> tasks;

    /**
     * Flag to stop bg threads
     */
    State state;

public:
    Executor(std::size_t low_watermark = 0, std::size_t hight_watermark = 10, std::size_t max_queue_size = 10,
             std::size_t idle_time = 1000);
    ~Executor(){};

    /**
     * Signal thread pool to stop, it will stop accepting new jobs and close threads just after each become
     * free. All enqueued jobs will be complete.
     *
     * In case if await flag is true, call won't return until all background jobs are done and all threads are stopped
     */
    void Stop(bool await = false);

    /**
     * Add function to be executed on the threadpool. Method returns true in case if task has been placed
     * onto execution queue, i.e scheduled for execution and false otherwise.
     *
     * That function doesn't wait for function result. Function could always be written in a way to notify caller about
     * execution finished by itself
     */
    template <typename F, typename... Types> bool Execute(F &&func, Types... args) {
        // Prepare "task"
        auto exec = std::bind(std::forward<F>(func), std::forward<Types>(args)...);

        std::unique_lock<std::mutex> lock(this->mutex);
        if (state != State::kRun) {
            return false;
        }

        // Enqueue new task
        if (tasks.size() < max_queue_size) {
            tasks.push_back(exec);
        } else {
            return false;
        }

        if (sleeping_workers == 0) {
            if (running_threads < hight_watermark) {

                std::thread thr(perform, this);
                thr.detach();
                running_threads++;
                sleeping_workers++;
                empty_condition.notify_one();
            }
        } else {
            empty_condition.notify_one();
        }
        return true;
    }
};

} // namespace Concurrency
} // namespace Afina

#endif // AFINA_CONCURRENCY_EXECUTOR_H
