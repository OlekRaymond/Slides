
#include <utility>

template<typename Derived>
struct BoundCheckedIndexLookups {
    template<typename _> friend class BoundCheckedIndexLookups;
    template<typename ...Args>
    auto at(Args... a) { return static_cast<Derived*>(this)->ContainerToForwardTo().at(a...); }
    template<typename ...Args>
    auto at(Args... a) const { return static_cast<Derived*>(this)->ContainerToForwardTo().at(a...); }
};
template<typename Derived>
struct Back {
    template<typename _> friend class BoundCheckedIndexLookups;
    template<typename ...Args>
    auto back(Args... a) { return static_cast<Derived*>(this)->ContainerToForwardTo().back(a...); }
    template<typename ...Args>
    auto back(Args... a) const { return static_cast<Derived*>(this)->ContainerToForwardTo().back(a...); }
};

template<typename Derived>
struct UncheckedIndexLookups {
    template<typename _> friend class BoundCheckedIndexLookups;
    template<typename Arg>
    auto operator[](Arg a) { return static_cast<Derived*>(this)->ContainerToForwardTo()[a]; }
    template<typename Arg>
    auto operator[](Arg a) const { return static_cast<Derived*>(this)->ContainerToForwardTo()[a]; }
};
template<typename Derived>
struct Emplace {
    template<typename _> friend class Emplace;
    template<typename ...Args>
    auto emplace(Args... a) { return static_cast<Derived*>(this)->ContainerToForwardTo().emplace(a...); }
};

#define Ray_Forward(name) template<typename ...Args> auto name (Args... a) { return static_cast<Derived*>(this)->ContainerToForwardTo(). name (std::forward<Args>(a)...); }
template<typename Derived>
struct EmplaceBack {
    Ray_Forward(emplace_back
    )
};

// Usage:
#include <vector>
struct VectorLike : EmplaceBack<VectorLike>, Back<VectorLike> {
protected:
    std::vector<int>& ContainerToForwardTo() { return to_name_forward; }
    friend EmplaceBack; friend Back;
private:
    std::vector<int> to_name_forward;
};

int main() {
    VectorLike v{};
    auto a = v.emplace_back(1);
    return v.back();
}

