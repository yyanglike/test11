#include <boost/spirit/include/qi.hpp>
#include <boost/spirit/include/phoenix_operator.hpp>
#include <boost/spirit/include/phoenix_function.hpp>
#include <vector>
#include <algorithm>
#include <iterator>

namespace qi = boost::spirit::qi;
namespace ascii = boost::spirit::ascii;
namespace phoenix = boost::phoenix;

// 移动平均线计算函数
std::vector<double> calculateMovingAverage(const std::vector<double>& data, int period)
{
    std::vector<double> result(data.size(), std::nan(""));
    double sum = 0.0;

    for (int i = 0; i < period; ++i)
    {
        sum += data[i];
    }

    result[period - 1] = sum / period;

    for (int i = period; i < data.size(); ++i)
    {
        sum = sum - data[i - period] + data[i];
        result[i] = sum / period;
    }

    return result;
}

// 乘法操作函数
std::vector<double> multiply(const std::vector<double>& a, const std::vector<double>& b)
{
    std::vector<double> result;
    result.reserve(a.size());

    for (size_t i = 0; i < a.size(); ++i)
    {
        if (std::isnan(a[i]) || std::isnan(b[i]))
            result.push_back(std::nan(""));
        else
            result.push_back(a[i] * b[i]);
    }

    return result;
}

// 移动平均线函数对象
struct calculate_moving_average_impl
{
    template <typename T1, typename T2>
    struct result { typedef std::vector<double> type; };

    std::vector<double> operator()(const std::vector<double>& data, int period) const
    {
        return calculateMovingAverage(data, period);
    }
};
phoenix::function<calculate_moving_average_impl> calculateMovingAverageFunc;

// 乘法操作函数对象
struct multiply_impl
{
    typedef std::vector<double> result_type;

    std::vector<double> operator()(const std::vector<double>& a, const std::vector<double>& b) const
    {
        return multiply(a, b);
    }
};
phoenix::function<multiply_impl> multiplyFunc;

// 解析器
template <typename Iterator>
struct calculator : qi::grammar<Iterator, ascii::space_type, std::vector<double>()>
{
    calculator() : calculator::base_type(expression)
    {
        expression =
            term                            [_val = _1]
            >> *(   ('*' >> term            [_val = multiplyFunc(_val, _1)])
                )
            ;

        term =
            factor                          [_val = _1]
            ;

        factor =
            ('[' >> qi::double_ % ',' >> ']' >> ',' >> qi::int_) 
                [ _val = calculateMovingAverageFunc(_1, _2) ]
            |   ('[' >> qi::double_ % ',' >> ']' )
                [ _val = _1 ]
            ;
    }

    qi::rule<Iterator, ascii::space_type, std::vector<double>()> expression, term, factor;
};

// 测试代码
int main()
{
    std::string str = "[1.0, 2.0, 3.0, 4.0, 5.0], 3 * [2.0, 2.0, 2.0, 2.0, 2.0]";
    calculator<std::string::const_iterator> calc;
    std::vector<double> result;
    std::string::const_iterator iter = str.begin();
    bool r = qi::phrase_parse(iter, str.end(), calc, ascii::space, qi::skip_flag::postskip, result);


    if (r && iter == str.end())
    {
        std::cout << "Parsing succeeded, result: ";
        std::copy(result.begin(), result.end(), std::ostream_iterator<double>(std::cout, " "));
        std::cout << std::endl;
    }
    else
    {
        std::cout << "Parsing failed" << std::endl;
    }

    return 0;
}
