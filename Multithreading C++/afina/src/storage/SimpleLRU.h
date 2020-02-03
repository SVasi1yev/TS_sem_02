#ifndef AFINA_STORAGE_SIMPLE_LRU_H
#define AFINA_STORAGE_SIMPLE_LRU_H

#include <map>
#include <memory>
#include <mutex>
#include <string>

#include <afina/Storage.h>

namespace Afina {
namespace Backend {
/**
 * # Map based implementation
 * That is NOT thread safe implementaiton!!
 */
class SimpleLRU : public Afina::Storage {
public:
    SimpleLRU(size_t max_size = 1024)
        : _max_size(max_size), _free_size(max_size), _lru_head(nullptr), _lru_tail(nullptr) {}

    ~SimpleLRU() {
        _lru_index.clear();
        // _lru_head.reset(); // TODO: Here is stack overflow
        while (_lru_tail != nullptr) {
            _lru_tail->next.reset();
            _lru_tail = _lru_tail->prev;
        }
        _lru_head.reset();
    }

    // Implements Afina::Storage interface
    bool Put(const std::string &key, const std::string &value) override;

    // Implements Afina::Storage interface
    bool PutIfAbsent(const std::string &key, const std::string &value) override;

    // Implements Afina::Storage interface
    bool Set(const std::string &key, const std::string &value) override;

    // Implements Afina::Storage interface
    bool Delete(const std::string &key) override;

    // Implements Afina::Storage interface
    bool Get(const std::string &key, std::string &value) override;

    // LRU cache node
    using lru_node = struct lru_node {
        const std::string key;
        std::string value;
        // std::unique_ptr<lru_node> prev;
        std::unique_ptr<lru_node> next;
        lru_node *prev;
    };

private:
    using lru_map =
        std::map<std::reference_wrapper<const std::string>, std::reference_wrapper<lru_node>, std::less<std::string>>;

    // Maximum number of bytes could be stored in this cache.
    // i.e all (keys+values) must be less the _max_size
    std::size_t _max_size;
    std::size_t _free_size;

    // Main storage of lru_nodes, elements in this list ordered descending by "freshness": in the head
    // element that wasn't used for longest time.
    //
    // List owns all nodes
    std::unique_ptr<lru_node> _lru_head;
    lru_node *_lru_tail;

    // Index of nodes from list above, allows fast random access to elements by lru_node#key
    lru_map _lru_index;

    lru_map::iterator MoveToHead(const std::string &key);

    bool PutInHead(const std::string &key, const std::string &value);
};

} // namespace Backend
} // namespace Afina

#endif // AFINA_STORAGE_SIMPLE_LRU_H
