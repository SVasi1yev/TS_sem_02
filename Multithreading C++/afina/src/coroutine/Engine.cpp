#include <afina/coroutine/Engine.h>

#include <setjmp.h>
#include <stdio.h>
#include <string.h>

namespace Afina {
namespace Coroutine {

void Engine::Store(context &ctx) {
    char stack_end;
    if (&stack_end > StackBottom) {
        ctx.Hight = &stack_end;
        ctx.Low = StackBottom;
    } else {
        ctx.Low = &stack_end;
        ctx.Hight = StackBottom;
    }

    char*& stack_buffer = std::get<0>(ctx.Stack);
    uint32_t &size = std::get<1>(ctx.Stack);
    uint32_t new_size = ctx.Hight - ctx.Low;
    if (new_size > size) {
        delete[] stack_buffer;
        stack_buffer = new char[new_size];
        size = new_size;
    }
    memcpy(ctx.Low, stack_buffer, new_size);
}

void Engine::Restore(context &ctx) {
    char stack_end;
    while ((&stack_end >= ctx.Low) && (&stack_end <= ctx.Hight)) {
        Restore(ctx);
    }

    memcpy(ctx.Low, std::get<0>(ctx.Stack), std::get<1>(ctx.Stack));
    longjmp(ctx.Environment, 1);
}

void Engine::yield() {
    if (cur_routine == alive && alive->next) {
        Enter(*(alive->next));
    } else if (cur_routine != alive && alive) {
        Enter(*alive);
    }
}

void Engine::sched(void *routine) {
    if (cur_routine == routine) {
        return;
    }

    if (routine) {
        Enter(*(static_cast<context *>(routine)));
    } else {
        yield();
    }
}

void Engine::Enter(context &ctx) {
    if (cur_routine && cur_routine != idle_ctx) {
        if (setjmp(cur_routine->Environment) > 0) {
            return;
        }
        Store(*cur_routine);
    }

    cur_routine = &ctx;
    Restore(ctx);
}

} // namespace Coroutine
} // namespace Afina
