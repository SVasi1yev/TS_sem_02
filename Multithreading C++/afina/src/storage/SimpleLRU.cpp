#include "SimpleLRU.h"
#include <iostream>

namespace Afina {
namespace Backend {

using lru_map = std::map<std::reference_wrapper<const std::string>, std::reference_wrapper<SimpleLRU::lru_node>,
                         std::less<std::string>>;

lru_map::iterator SimpleLRU::MoveToHead(const std::string &key) {
    auto remove_node_ptr = this->_lru_index.find(key);
    if (remove_node_ptr == this->_lru_index.end()) {
        return remove_node_ptr;
    }
    lru_node &remove_node = remove_node_ptr->second;
    if (this->_lru_head->key == key) {
        return remove_node_ptr;
    }
    if (remove_node.next != nullptr) {
        remove_node.next->prev = remove_node.prev;
    } else {
        this->_lru_tail = remove_node.prev;
    }
    this->_lru_head->prev = &remove_node;
    remove_node.prev->next.release();
    remove_node.prev->next = std::move(remove_node.next);
    remove_node.next = std::move(this->_lru_head);
    this->_lru_head.reset(&remove_node);
    if (remove_node.prev->prev == nullptr) {
        remove_node.prev->prev = this->_lru_head.get();
    }
    remove_node.prev = nullptr;
    return remove_node_ptr;
}

bool SimpleLRU::PutInHead(const std::string &key, const std::string &value) {
    std::size_t new_node_size = key.length() + value.length();
    if (new_node_size > this->_max_size) {
        return false;
    }
    while (this->_free_size < new_node_size) {
        SimpleLRU::Delete(_lru_tail->key);
    }
    if (this->_lru_head == nullptr) {
        this->_lru_head.reset(new lru_node{key, value, nullptr, nullptr});
        this->_lru_tail = this->_lru_head.get();
    } else {
        std::unique_ptr<lru_node> new_head(new lru_node{key, value, nullptr, nullptr});
        this->_lru_head->prev = new_head.get();
        new_head->next = std::move(this->_lru_head);
        this->_lru_head = std::move(new_head);
    }
    this->_lru_index.emplace(std::make_pair(std::ref((*(this->_lru_head)).key), std::ref(*(this->_lru_head))));
    this->_free_size -= new_node_size;
    return true;
}

// See MapBasedGlobalLockImpl.h
bool SimpleLRU::Put(const std::string &key, const std::string &value) {
    auto it = SimpleLRU::MoveToHead(key);
    if (it == _lru_index.end()) {
        return SimpleLRU::PutInHead(key, value);
    } else {
        std::size_t new_node_size = key.length() + value.length();
        if (new_node_size > this->_max_size) {
            return false;
        }
        std::int64_t delta_size = new_node_size - (it->second.get().key.length() + it->second.get().value.length());
        while (this->_free_size < delta_size) {
            SimpleLRU::Delete(_lru_tail->key);
        }
        _free_size -= delta_size;
        it->second.get().value = value;
        return true;
    }
}

// See MapBasedGlobalLockImpl.h
bool SimpleLRU::PutIfAbsent(const std::string &key, const std::string &value) {
    auto it = this->_lru_index.find(key);
    if (it != this->_lru_index.end()) {
        return false;
    }
    return SimpleLRU::PutInHead(key, value);
}

// See MapBasedGlobalLockImpl.h
bool SimpleLRU::Set(const std::string &key, const std::string &value) {
    auto it = SimpleLRU::MoveToHead(key);
    if (it == this->_lru_index.end()) {
        return false;
    }
    std::size_t new_node_size = key.length() + value.length();
    if (new_node_size > this->_max_size) {
        return false;
    }
    std::int64_t delta_size = new_node_size - (it->second.get().key.length() + it->second.get().value.length());
    while (this->_free_size < delta_size) {
        SimpleLRU::Delete(_lru_tail->key);
    }
    _free_size -= delta_size;
    it->second.get().value = value;
    return true;
}

// See MapBasedGlobalLockImpl.h
bool SimpleLRU::Delete(const std::string &key) {
    auto remove_node_ptr = this->_lru_index.find(key);
    if (remove_node_ptr == this->_lru_index.end()) {
        return false;
    }
    lru_node &remove_node = remove_node_ptr->second;
    std::size_t remove_node_size = remove_node.key.length() + remove_node.value.length();
    this->_free_size += remove_node_size;
    this->_lru_index.erase(remove_node_ptr);
    if (remove_node.next != nullptr) {
        remove_node.next->prev = remove_node.prev;
    } else {
        this->_lru_tail = remove_node.prev;
    }
    if (remove_node.prev != nullptr) {
        remove_node.prev->next = std::move(remove_node.next);
    } else {
        this->_lru_head = std::move(remove_node.next);
    }
    return true;
}

// See MapBasedGlobalLockImpl.h
bool SimpleLRU::Get(const std::string &key, std::string &value) {
    auto it = SimpleLRU::MoveToHead(key);
    if (it != this->_lru_index.end()) {
        value = it->second.get().value;
        return true;
    }
    return false;
}

} // namespace Backend
} // namespace Afina
