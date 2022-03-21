#!/usr/bin/env python
#!-*- coding:utf-8 -*-

import collections
from math import ceil
from django.utils import six 

import time
import uuid
import datetime
from collections import heapq
import math
from time import sleep


""" 
	ceil(...): ceil(x)
    
    Return the ceiling of x as a float.
    This is the smallest integral value >= x.

    意思是ceil(x)返回大于或等于x的最小的float型数字，比如：ceil(2)-->2.0, ceil(2.1)-->3.0
"""

# django.utils.six - Utilities for writing code that runs on Python 2 and 3
# from django.utils import six 

"""
	分别定义了InvalidPage, PageNotAnInteger, EmptyPage三个异常类型。
"""
class InvalidPage(Exception):
    pass


class PageNotAnInteger(InvalidPage):
    pass


class EmptyPage(InvalidPage):
    pass


class Paginator(object):
	"""
		object_list: 定义用于存放对象的容器，可以为list, tuple, django QuerySet, 或者是带有count()or__len__()方法的切片对象。
		per_page: 规定每页显示item的数量，这个数量不包括orphans。
		orphans: 最后一页显示的item的数量要大于设置的orphans的值。
		{
			假如设置orphans=5，如果最后一页item的数量不大于5的话，则会将最后一页中的item添加到前一页中显示，
			这时候前一页就变成了最后一页。
			orphans参数的设置是为了满足这样的情况：如果你不想在最后一页显示很少量的item的话，你就可以将这些少量的item合并到前一页中，
			然后舍弃最后一页。前一页此时就变成了最后一页。
		}
		allow_empty_first_page: 是否允许第一页为空，默认允许第一页为空，即没有要显示的item
	"""

    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True):
        self.object_list = object_list
        self.per_page = int(per_page)
        self.orphans = int(orphans)
        self.allow_empty_first_page = allow_empty_first_page
        self._num_pages = self._count = None   # 初始化 _num_pages与_count为None

    def validate_number(self, number):
        """
        验证传递过来的页数索引（第几页）的合法性，
        返回合法的页数索引（第几页）。
        """
        try:
            number = int(number) # 验证是否为int型
        except (TypeError, ValueError):
            raise PageNotAnInteger('That page number is not an integer')
        if number < 1: # 不可能存在小于1的显示页
            raise EmptyPage('That page number is less than 1')
        if number > self.num_pages:# 没有item要显示，num_pages为0，但允许第一页为空，所以输入1是合法的
            if number == 1 and self.allow_empty_first_page:
                pass
            else:
                raise EmptyPage('That page contains no results')
        return number

    def page(self, number):
        """
       	返回当前输入页的Page对象。

       	解读这个函数：
		假设object_list包含23个items，per_page=8(每页最多显示8条item)，orphans=3（设置最后一页显示的item数目要大于3），
		这样以来，显示的结果为：[1, 2, 3] --> 8，8，7。
		假设传入的是number=2，表示第二页。
		bottom = (2 - 1) * 8 = 8  表示当前页之前的所有页已经显示的item数量
		top = bottom + self.per_page = 8 + 8 = 16
		top + 3 = 16 + 3 = 19 不大于 self.count=23，所以第二页显示的列表对象则为object_list[8:16]. 
		判断 top + self.orphans >= self.count 
		表示的意思是：当前页以及之前所有的页包含的item的数量+最后一页orphans的显示数目 大于或等于 整个项目的数量时，
		这时最后一页就不需要了，可以把最后一页少量的项目添加到前一页中进行显示。
        """
        number = self.validate_number(number) # 验证输入的页数索引的合法性
        bottom = (number - 1) * self.per_page 
        
        top = bottom + self.per_page
        if top + self.orphans >= self.count: # 假设最后一页能够显示orphans个item，判断item的总数目count与
        				     # 满足该假设所需要的item的数目，一旦count<=top+orphans，则说明
        				     # 实际的item数目在最后一页显示的数目是不会大于orphans的，这种情况下，
        				     # 最后一页就要被舍弃，则当前页显示的item为object_list[bottom:top]
            top = self.count
        
        # return Page(object_list[bottom:top], number, 当前Paginator对象的引用)
        return self._get_page(self.object_list[bottom:top], number, self)


    def _get_page(self, *args, **kwargs):
        """
        Returns an instance of a single page.

        This hook can be used by subclasses to use an alternative to the
        standard :cls:`Page` object.
        """
        return Page(*args, **kwargs)

    def _get_count(self):
        """
        得到要显示的item的总数目
        """
        if self._count is None:
            try:
                self._count = self.object_list.count()
            except (AttributeError, TypeError):
                # AttributeError if object_list has no count() method.
                # TypeError if object_list.count() requires arguments
                # (i.e. is of type list).
                self._count = len(self.object_list)
        return self._count
    count = property(_get_count) # property()表示可以以属性的方式来调用函数

    def _get_num_pages(self):
        """
        得到显示所有items的总页数。
        """
        if self._num_pages is None:
        	# 如果item的总数为0，且不允许第一页为空，则显示的总页数为0
            if self.count == 0 and not self.allow_empty_first_page:
                self._num_pages = 0
            else:
            	'''
            	self.count-self.orphans意思是假定最后一页显示的item数量为设置的orphans的值。
            	此时最后一页是已经要被舍弃的了（最后一页的项目会添加到前一页中去）。
            	判断显示item需要页数的重点就是（count-orphans）个item所需要的显示页数。因为最后一页已经是不存在的了，那么
            	显示（count-orphans）个item需要的页数，就是显示整个item需要的页数。
		ceil(hits / float(self.per_page))：之差的结果/每页显示的最多的数量，并对此取整得到相应的值，
		此算法的巧妙之处就在于先做了self.count-self.orphans的运算。
            	'''
                hits = max(1, self.count - self.orphans)
                self._num_pages = int(ceil(hits / float(self.per_page)))
        return self._num_pages
    num_pages = property(_get_num_pages)

    def _get_page_range(self):
        """
        获取显示items的页数的范围，从第1页 ---> 第num_pages页
        Returns a 1-based range of pages for iterating through within
        a template for loop.
        """
        return list(six.moves.range(1, self.num_pages + 1))
    page_range = property(_get_page_range)


QuerySetPaginator = Paginator   # For backwards-compatibility.


class Page(collections.Sequence):

    def __init__(self, object_list, number, paginator):
        self.object_list = object_list
        self.number = number
        self.paginator = paginator

    def __repr__(self):
        return '<Page %s of %s>' % (self.number, self.paginator.num_pages)

    def __len__(self):
        return len(self.object_list)

    def __getitem__(self, index):
        if not isinstance(index, (slice,) + six.integer_types):
            raise TypeError
        # The object_list is converted to a list so that if it was a QuerySet
        # it won't be a database hit per __getitem__.
        if not isinstance(self.object_list, list):
            self.object_list = list(self.object_list)
        return self.object_list[index]

    def has_next(self):
        return self.number < self.paginator.num_pages # 判断输入当前页是否小于总页数

    def has_previous(self):
        return self.number > 1

    def has_other_pages(self):
        return self.has_previous() or self.has_next()

    def next_page_number(self):
        return self.paginator.validate_number(self.number + 1)

    def previous_page_number(self):
        return self.paginator.validate_number(self.number - 1)

    def start_index(self):
        """
        返回当前页的第一个item的index值。
        Returns the 1-based index of the first object on this page,
        relative to total objects in the paginator.
        """
        # Special case, return zero if no items.
        if self.paginator.count == 0:
            return 0
        return (self.paginator.per_page * (self.number - 1)) + 1

    def end_index(self):
        """
       	返回当前页的最后一个item的index值。
        Returns the 1-based index of the last object on this page,
        relative to total objects found (hits).
        """
        # Special case for the last page because there can be orphans.
        if self.number == self.paginator.num_pages:
            return self.paginator.count
        return self.number * self.paginator.per_page
