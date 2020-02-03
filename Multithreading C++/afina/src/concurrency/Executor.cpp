#include <afina/concurrency/Executor.h>

namespace Afina {
namespace Concurrency {

void perform(Executor *executor) {
    auto last_task_time = std::chrono::system_clock::now(), now = last_task_time;
    std::function<void()> task_to_perform;
    while (true) {
        {
            std::unique_lock<std::mutex> lock(executor->mutex);
            while (executor->tasks.empty() && executor->state == Executor::State::kRun &&
                   std::chrono::duration_cast<std::chrono::milliseconds>(now - last_task_time) < executor->idle_time) {
                executor->empty_condition.wait_for(lock, executor->idle_time);
                now = std::chrono::system_clock::now();
            }
            executor->sleeping_workers--;
            if (!executor->tasks.empty()) {
                task_to_perform = executor->tasks.front();
                executor->tasks.pop_front();
            } else {
                if (executor->state != Executor::State::kRun) {
                    executor->running_threads--;
                    if (executor->running_threads == 0) {
                        executor->state = Executor::State::kStopped;
                        executor->empty_condition.notify_one();
                    }
                    return;
                }
                if (executor->sleeping_workers >= executor->low_watermark) {
                    executor->running_threads--;
                    return;
                }
                executor->sleeping_workers++;
                continue;
            }
        }
        try {
            task_to_perform();
        } catch (...) {
        }
        last_task_time = std::chrono::system_clock::now();
        std::unique_lock<std::mutex> lock(executor->mutex);
        executor->sleeping_workers++;
    }
}

Executor::Executor(std::size_t low_watermark, std::size_t hight_watermark, std::size_t max_queue_size,
                   std::size_t idle_time)
    : low_watermark(low_watermark), hight_watermark(hight_watermark), max_queue_size(max_queue_size),
      idle_time(idle_time) {
    std::unique_lock<std::mutex> lock(mutex);
    for (size_t i = 0; i < low_watermark; i++) {
        std::thread thr(perform, this);
        thr.detach();
    }
    running_threads = low_watermark;
    sleeping_workers = low_watermark;

    state = State::kRun;
}

void Executor::Stop(bool await) {
    std::unique_lock<std::mutex> lock(mutex);
    state = State::kStopping;
    empty_condition.notify_all();
    if (await) {
        while (running_threads > 0) {
            empty_condition.wait(lock);
        }
    }
}

} // namespace Concurrency
} // namespace Afina