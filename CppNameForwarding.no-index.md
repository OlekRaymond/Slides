```C++
#include <utility>

#define Ray_Forward_non_const(name) \
    template<typename ...Args> \
    constexpr decltype(auto) name (Args... a) { \
        return static_cast<Derived*>(this)->ContainerToForwardTo(). \
         name (std::forward<Args>(a)...); \
    }
#define Ray_Forward_const(name) \
    template<typename ...Args> \
    constexpr decltype(auto) name (Args... a) const { \
        return static_cast<Derived*>(this)->ContainerToForwardTo(). \
         name (std::forward<Args>(a)...); \
    }

#define Ray_Forward(name) Ray_Forward_non_const(name) Ray_Forward_const(name)

template<typename Derived> struct BoundCheckedIndexLookups { Ray_Forward(at); };
template<typename Derived> struct Back { Ray_Forward(back); };
template<typename Derived> struct Emplace { Ray_Forward_non_const(emplace) };
template<typename Derived> struct EmplaceBack { Ray_Forward_non_const(emplace_back) };
template<typename Derived> struct Iterators { Ray_Forward(end); Ray_Forward(begin); Ray_Forward(cend); Ray_Forward(cbegin); Ray_Forward(rend); Ray_Forward(rbegin); };
template<typename Derived> struct Size { Ray_Forward(size) };


#define Ray_Forward_const_bool_like_operator(symbols) \
    bool operator symbols (const Derived& d) const { \
        return static_cast<const Derived*>(this)->ToForwardTo() symbols d.ToForwardTo(); \
    }
template<typename Derived>
struct Equal { Ray_Forward_const_bool_like_operator(==) };
template<typename Derived>
struct Less { Ray_Forward_const_bool_like_operator(<) };
template<typename Derived>
struct Greater { Ray_Forward_const_bool_like_operator(>) };
template<typename Derived>
struct GreaterOrEqual { Ray_Forward_const_bool_like_operator(>=) };
template<typename Derived>
struct LessOrEqual { Ray_Forward_const_bool_like_operator(<=) };
template<typename Derived>
struct NotEqual { Ray_Forward_const_bool_like_operator(!=) };

template<typename Derived>
struct SpaceShip17 : Equal<Derived>, Less<Derived>, Greater<Derived>, GreaterOrEqual<Derived>, LessOrEqual<Derived>, NotEqual<Derived> {};

#if __cplusplus >= 202002L
template<typename Derived>
struct SpaceShip20 {
    Ray_Forward_const_bool_like_operator(==) // non-defaulted spaceships must have equality operators
    auto operator<=>(const Derived& d) const { return static_cast<const Derived*>(this)->ToForwardTo() <=> d.ToForwardTo(); }
};
    template <typename Derived>
    using SpaceShip = SpaceShip20<Derived>;
#else
    template <typename Derived>
    using SpaceShip = SpaceShip17<Derived>;
#endif

template<typename Derived>
struct IndexOperator {
    template<typename Arg>
    auto operator[](Arg a) { return static_cast<Derived*>(this)->ContainerToForwardTo()[a]; }
    template<typename Arg>
    const auto& operator[](Arg a) const { return static_cast<const Derived*>(this)->ContainerToForwardTo()[a]; }
};
// Lots can be added togeather
template<typename Derived>
struct Vector : EmplaceBack<Derived>, 
                Emplace<Derived>,
                Back<Derived>,
                SpaceShip<Derived>,
                Iterators<Derived>,
                BoundCheckedIndexLookups<Derived>
                Size<Derived>
{};


/// Contains functions to aid in usage
namespace identity {

#define Ray_Forward_PREFER_VAR(var_name, identity_type) \
template<typename Derived> \
struct PreferVar_ ## var_name ## _ ## identity_type { \
    constexpr const auto& identity_type ## ToForwardTo() const { return static_cast<const Derived*>(this)-> var_name; } \
    constexpr auto& identity_type ## ToForwardTo() { return static_cast<Derived*>(this)-> var_name ; } \
}

Ray_Forward_PREFER_VAR(toForwardTo, );
Ray_Forward_PREFER_VAR(toForwardTo, Container );

#undef Ray_Forward_PREFER_VAR
}
```






Following might be a better way of getting the thing?
```C++
template<typename T>
struct UserStruct {
    template<typename t>
    struct ToForward {
        t i;
        T j;
    };
    ToForward<int> toForward;
};
```










