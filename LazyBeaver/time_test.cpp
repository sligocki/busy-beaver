#include <fstream>
#include <iostream>
#include <map>
#include <string>

int main(int argc, char **argv)
{
  long long int limit;
  double acc;

  limit = std::stoll(argv[1]);

  acc = 0;
  for (long long int i = 0; i < limit; i++)
  {
    acc += i*i*i;
  }

  std::cout << acc << std::endl;
}
